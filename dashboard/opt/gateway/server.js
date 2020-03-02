var express = require('express');
var basic_auth = require('express-basic-auth')
var session = require('express-session');
var proxy = require('http-proxy-middleware');
var uuid = require('uuid');
var http = require('http');
var https = require('https');
var axios = require('axios');
var path = require('path');
var url = require('url');
var fs = require('fs');
var morgan = require('morgan')
var logger = require('./logger');
var config = require('./config');

var gateway_config = config.gateway_config;

var enable_webdav = process.env.ENABLE_WEBDAV;

// Setup the root application. Everything will actually be under a
// mount point corresponding to the specific user. This is added in
// each of the routes when defined.

var app = express();

var uri_root_path = process.env.URI_ROOT_PATH || '';

// Add logging for request.

var log_format = process.env.LOG_FORMAT || 'dev';

app.use(morgan(log_format));

// In OpenShift we are always behind a proxy, so trust the headers sent.

app.set('trust proxy', true);

// Short circuit WebDAV access as it handles its own authentication.

if (enable_webdav == 'true') {
    app.use(uri_root_path + '/webdav/', proxy({
        target: 'http://127.0.0.1:10084',
        ws: true
    }));
}

// Enable use of a client session for the user. This is used to track
// whether the user has logged in when using oauth. Session will expire
// after 24 hours.

var handshakes = {}

app.use(session({
    name: 'workshop-session-id',
    genid: function(req) {
        return uuid.v4()
    },
    secret: uuid.v4(),
    cookie: {
        path: uri_root_path,
        maxAge: 24*60*60*1000
    },
    resave: false,
    saveUninitialized: true
}));

// For standalone container deployment, provide the ability to enable
// authentication using HTTP Basic authentication. In this case there
// will be no user object added to the client session.

var auth_username = process.env.AUTH_USERNAME;
var auth_password = process.env.AUTH_PASSWORD;

async function install_basic_auth() {
    logger.info('Register basic auth handler');

    app.use(basic_auth({
        challenge: true,
        realm: 'Terminal',
        authorizer: function (username, password) {
            return username == auth_username && password == auth_password;
        }
    }));
}

// For OAuth access a handshake is perform against the portal web
// application. This mode of operation is setup by the following
// environment variables.

var portal_client_id = process.env.PORTAL_CLIENT_ID;
var portal_client_secret = process.env.PORTAL_CLIENT_SECRET;
var portal_api_url = process.env.PORTAL_API_URL;

var dashboard_url = process.env.DASHBOARD_URL;

var session_name = process.env.SESSION_NAME;

// These functions provide details on the project the deployment is,
// the service account name and the service token. These are only used
// when using OpenShift OAuth and rely on the service account details
// being mounted into the container.

function project_name() {
    const account_path = '/var/run/secrets/kubernetes.io/serviceaccount';
    const namespace_path = path.join(account_path, 'namespace');

    return fs.readFileSync(namespace_path, 'utf8');
}

function service_account_name(name) {
    const prefix = 'system:serviceaccount';
    const namespace = project_name();

    return prefix + ':' + namespace + ':' + name;
}

function service_account_token() {
    const account_path = '/var/run/secrets/kubernetes.io/serviceaccount';
    const token_path = path.join(account_path, 'token');

    return fs.readFileSync(token_path, 'utf8');
}

// OAuth servers support a well known URL for querying properties of the
// OAuth server. Unfortunately JupyterHub doesn't support this, so we
// need to fake up this data later. We can use this for the case when
// using OpenShift OAuth.

async function get_oauth_metadata(server) {
    const options = {
        baseURL: server,
        httpsAgent: new https.Agent({ rejectUnauthorized: false }),
        responseType: 'json'
    };

    const url = '/.well-known/oauth-authorization-server';

    return (await axios.get(url, options)).data;
}

function setup_oauth_credentials(metadata, client_id, client_secret) {
    var credentials = {
        client: {
            id: client_id,
            secret: client_secret
        },
        auth: {
            tokenHost: metadata['issuer'],
            authorizePath: metadata['authorization_endpoint'],
            tokenPath: metadata['token_endpoint']
        },
        options: {
            authorizationMethod: 'body',
        },
        http: {
            rejectUnauthorized: false
        }
    };

    return credentials;
}

// When using OAuth against the portal, after the user has authenticated,
// access the details of the session. We will be permitted if we are
// the owner or a staff member.

async function get_session_details(access_token) {
    const options = {
        baseURL: portal_api_url,
        headers: { 'Authorization': 'Bearer ' + access_token },
        responseType: 'json'
    };

    const url = '/workshops/session/' + session_name + '/authorize/';

    return (await axios.get(url, options)).data;
}

async function verify_session_access(access_token) {
    var details = await get_session_details(access_token);

    logger.info('Session details', details);

    return details.owner;
}

// Setup the OAuth callback that the OAuth server makes a request
// against to deliver the access code when authentication has been
// successful.

function register_oauth_callback(oauth2, verify_user) {
    logger.info('Register OAuth callback');

    app.get(uri_root_path + '/oauth_callback', async (req, res) => {
        try {
            var code = req.query.code;
            var state = req.query.state;

            // If we seem to have no record of the specific handshake
            // state, redirect back to the main page and start over.

            if (handshakes[state] === undefined) {
                return res.redirect(uri_root_path + '/');
            }

            // This retrieves the next URL to redirect to from the session
            // for this particular oauth handshake.

            var next_url = handshakes[state];
            delete handshakes[state];

            // Obtain the user access token using the authorization code.

            var redirect_uri;

            if (!dashboard_url) {
                redirect_uri = [req.protocol, '://', req.get('host'),
                    uri_root_path, '/oauth_callback'].join('');
            } else {
                redirect_uri = [dashboard_url, uri_root_path,
                    '/oauth_callback'].join('');
            }

            var options = {
                redirect_uri: redirect_uri,
                scope: 'user:info',
                code: code
            };

            logger.debug('token_options', {options:options});

            var auth_result = await oauth2.authorizationCode.getToken(options);
            var token_result = oauth2.accessToken.create(auth_result);

            logger.debug('auth_result', {result:auth_result});
            logger.debug('token_result', {result:token_result['token']});

            // Now we need to verify whether this user is allowed access
            // to the project.

            req.session.user = await verify_user(
                token_result['token']['access_token']);

            if (!req.session.user) {
                return res.status(403).json('Access forbidden');
            }

            logger.info('User access granted', {name:req.session.user});

            return res.redirect(next_url);
        } catch(err) {
            console.error('Error', err.message);
            return res.status(500).json('Authentication failed');
        }
    });
}

// Setup up redirection to the OAuth server authorization endpoint.

function register_oauth_handshake(oauth2) {
    logger.info('Register OAuth handshake');

    app.get(uri_root_path + '/oauth_handshake', (req, res) => {
        // Stash the next URL after authentication in the user session
        // keyed by unique code for this oauth handshake. Use the code
        // as the state for oauth requests.

        var state = uuid.v4();
        handshakes[state] = req.query.next;

        var redirect_uri;

        if (!dashboard_url) {
            redirect_uri = [req.protocol, '://', req.get('host'),
                uri_root_path, '/oauth_callback'].join('');
        } else {
            redirect_uri = [dashboard_url, uri_root_path,
                '/oauth_callback'].join('');
        }

        const authorization_uri = oauth2.authorizationCode.authorizeURL({
            redirect_uri: redirect_uri,
            scope: 'user:info',
            state: state
        });

        logger.debug('authorization_uri', {uri:authorization_uri});

        res.redirect(authorization_uri);
    });

    app.use(function (req, res, next) {
        if (!req.session.user) {
            next_url = encodeURIComponent(req.url);
            res.redirect(uri_root_path + '/oauth_handshake?next=' + next_url);
        }
        else {
            next();
        }
    })
}

// Setup routes etc, corresponding to requirements of different possible
// authentication methods used.

async function install_portal_auth() {
    var issuer = portal_api_url;

    var client_id = portal_client_id;
    var client_secret = portal_client_secret;

    var api_url = url.parse(portal_api_url);

    var metadata = {
        issuer: issuer,
        authorization_endpoint: issuer + '/oauth2/authorize',
        token_endpoint: issuer + '/oauth2/token'
    };

    logger.info('OAuth server metadata', {metadata:metadata});

    var credentials = setup_oauth_credentials(metadata, client_id,
        client_secret);

    logger.info('OAuth server credentials', {credentials:credentials});

    var oauth2 = require('simple-oauth2').create(credentials);

    register_oauth_callback(oauth2, verify_session_access);
    register_oauth_handshake(oauth2);
}

async function setup_access() {
    if (portal_client_id) {
        logger.info('Install portal oauth support');
        await install_portal_auth();
    }
    else if (auth_username) {
        if (auth_username != '*') {
            logger.info('Install HTTP Basic auth support');
            await install_basic_auth();
        }
        else {
            logger.info('All authentication has been disabled');
        }
    }
}

// Setup intercepts for proxying to internal application ports.

function setup_proxy() {
    const filter = function(pathname, req) {
        if (!gateway_config["proxies"]) {
            return false;
        }

        let host = req.get('host');

        if (!host) {
            return false;
        } 

        let node = host.split('.')[0];
        let proxies = gateway_config["proxies"];

        for (let i=0; i<proxies.length; i++) {
            let proxy = proxies[i];
            if (node.endsWith('-'+proxy["name"])) {
                return true;
            }
        }

        return false;
    }

    function router(req) {
        let host = req.get('host');
        let node = host.split('.')[0];
        let proxies = gateway_config["proxies"];

        for (let i=0; i<proxies.length; i++) {
            let proxy = proxies[i];
            if (node.endsWith('-'+proxy["name"])) {
                return {
                    protocol: 'http:',
                    host: 'localhost',
                    port: proxy['port'],
                    ws: true
                }
            }
        }
    }

    app.use(proxy(filter, {
        target: 'http://localhost',
        router: router,
        ws: true
    }));
}

// Setup handler for default page and routes. If no overrides of any
// sort are defined then redirect to /terminal.

function set_default_page() {
    var default_route = process.env.DEFAULT_ROUTE || '/terminal';

    var default_index = path.join(__dirname, 'routes', 'index.js');
    var override_index = '/home/eduk8s/workshop/gateway/routes/index.js';

    if (fs.existsSync(override_index)) {
        logger.info('Set index to', {path:override_index}); 
        app.get('^' + uri_root_path + '/?$', require(override_index));
    }
    else if (fs.existsSync(default_index)) {
        logger.info('Set index to', {path:default_index}); 
        app.get('^' + uri_root_path + '/?$', require(default_index));
    }
    else {
        logger.info('Set index to', {path:default_route}); 
        app.get('^' + uri_root_path + '/?$', function (req, res) {
            res.redirect(uri_root_path + default_route);
        });
    }
}

function install_routes(directory) {
    if (fs.existsSync(directory)) {
        var files = fs.readdirSync(directory);

        for (var i=0; i<files.length; i++) {
            var filename = files[i];

            if (filename.endsWith('.js')) {
                var basename = filename.split('.').slice(0, -1).join('.');

                if (basename != 'index') {
                    var prefix = uri_root_path + '/' + basename;

                    app.get('^' + prefix + '$', function (req, res) {
                        res.redirect(url.parse(req.url).pathname + '/');
                    });

                    var pathname = path.join(directory, filename);
                    var router = require(pathname)(app, prefix + '/');

                    logger.info('Install route for', {path:pathname});

                    app.use(prefix + '/', router);
                }
            }
        }
    }
}

function setup_routing() {
    set_default_page();

    install_routes(path.join(__dirname, 'routes'));
    install_routes('/home/eduk8s/workshop/gateway/routes');
}

// Start the listener.

function start_listener() {
    logger.info('Start listener');

    app.listen(10080);
}

// Setup everything and start listener.

async function main() {
    try {
        await setup_access();
        setup_proxy();
        setup_routing();
        start_listener();
    } catch (err) {
        logger.error('ERROR', err);
    }
}

main();
