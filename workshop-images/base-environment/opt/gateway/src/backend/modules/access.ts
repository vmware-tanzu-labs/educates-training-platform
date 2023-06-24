import * as express from "express"
import * as basic_auth from "express-basic-auth"
import * as fs from "fs"
import * as path from "path"
import * as https from "https"
import { v4 as uuidv4 } from "uuid"

const axios = require("axios").default

import { logger } from "./logger"

// For standalone container deployment of workshop, provide the ability to
// enable authentication using HTTP Basic authentication. In this case there
// will be no user object added to the client session.

const AUTH_USERNAME = process.env.AUTH_USERNAME
const AUTH_PASSWORD = process.env.AUTH_PASSWORD

async function install_basic_auth(app: express.Application) {
    logger.info("Register basic auth handler")

    app.use(basic_auth({
        challenge: true,
        realm: "Terminal",
        authorizer: (username: string, password: string) => {
            return username == AUTH_USERNAME && password == AUTH_PASSWORD
        }
    }))
}

// For OAuth access a handshake is perform against the portal web application.
// This mode of operation is setup by the following environment variables.

const PORTAL_CLIENT_ID = process.env.PORTAL_CLIENT_ID
const PORTAL_CLIENT_SECRET = process.env.PORTAL_CLIENT_SECRET
const PORTAL_URL = process.env.PORTAL_URL
const PORTAL_API_URL = process.env.PORTAL_API_URL

const INGRESS_PROTOCOL = process.env.INGRESS_PROTOCOL

const SESSION_NAME = process.env.SESSION_NAME

// These functions provide details on the project the deployment is, the
// service account name and the service token. These are only used when using
// cluster OAuth and rely on the service account details being mounted into
// the container.

function project_name(): string {
    const account_path = "/var/run/secrets/kubernetes.io/serviceaccount"
    const namespace_path = path.join(account_path, "namespace")

    return fs.readFileSync(namespace_path, "utf8")
}

function service_account_name(name: string): string {
    const prefix = "system:serviceaccount"
    const namespace = project_name()

    return prefix + ":" + namespace + ":" + name
}

function service_account_token(): string {
    const account_path = "/var/run/secrets/kubernetes.io/serviceaccount"
    const token_path = path.join(account_path, "token")

    return fs.readFileSync(token_path, "utf8")
}

// When using OAuth against the portal, after the user has authenticated,
// access the details of the session. We will be permitted if we are
// the owner or a staff member.

async function get_session_authorization(access_token: string) {
    const options = {
        baseURL: PORTAL_API_URL,
        headers: { "Authorization": "Bearer " + access_token },
        responseType: "json"
    };

    const url = "/workshops/session/" + SESSION_NAME + "/authorize/"

    return (await axios.get(url, options)).data
}

async function verify_session_access(access_token: string) {
    var details = await get_session_authorization(access_token)

    logger.info("Session details", details)

    return details
}

// Setup the OAuth callback that the OAuth server makes a request against to
// deliver the access code when authentication has been successful.

let handshakes = {}

function register_oauth_callback(app: express.Application, oauth2: any, verify_user: any) {
    logger.info("Register OAuth callback.")

    app.get("/oauth_callback", async (req, res) => {
        try {
            let code: string = <string>req.query.code
            let state: string = <string>req.query.state

            // If we seem to have no record of the specific handshake state,
            // redirect back to the main page and start over.

            if (handshakes[state] === undefined)
                return res.redirect("/")

            // This retrieves the next URL to redirect to from the session for
            // this particular oauth handshake.

            let next_url = handshakes[state]

            delete handshakes[state]

            // Obtain the user access token using the authorization code.

            let redirect_uri = [INGRESS_PROTOCOL, "://", req.get("host"),
                "/oauth_callback"].join("")

            var options = {
                redirect_uri: redirect_uri,
                scope: "user:info",
                code: code
            }

            logger.debug("token_options", { options: options })

            var auth_result = await oauth2.authorizationCode.getToken(options)
            var token_result = oauth2.accessToken.create(auth_result)

            logger.debug("auth_result", { result: auth_result })
            logger.debug("token_result", { result: token_result["token"] })

            // Now we need to verify whether this user is allowed access
            // to the project.

            req.session.identity = await verify_user(
                token_result["token"]["access_token"])

            if (!req.session.identity)
                return res.status(403).json("Access forbidden")

            req.session.access_token = token_result["token"]["access_token"]
            req.session.refresh_token = token_result["token"]["refresh_token"]

            req.session.started = (new Date()).toISOString()

            logger.info("User access granted", req.session.identity)

            return res.redirect(next_url)
        } catch (error) {
            logger.error('Unexpected error occurred', error.message)

            return res.status(500).json("Authentication failed")
        }
    })
}

// Setup up redirection to the OAuth server authorization endpoint.

function register_oauth_handshake(app: express.Application, oauth2: any) {
    logger.info("Register OAuth handshake")

    app.get("/oauth_handshake", (req, res) => {
        // Stash the next URL after authentication in the user session keyed
        // by unique code for this oauth handshake. Use the code as the state
        // for oauth requests.

        let state = uuidv4()

        handshakes[state] = req.query.next

        let redirect_uri = [INGRESS_PROTOCOL, "://", req.get("host"),
            "/oauth_callback"].join("")

        const authorization_uri = oauth2.authorizationCode.authorizeURL({
            redirect_uri: redirect_uri,
            scope: "user:info",
            state: state
        });

        logger.debug('authorization_uri', { uri: authorization_uri })

        res.redirect(authorization_uri)
    })

    app.use((req, res, next) => {
        if (!req.session.identity) {
            let next_url: string = encodeURIComponent(req.url)
            res.redirect("/oauth_handshake?next=" + next_url)
        }
        else {
            next()
        }
    })
}

// Preferred method of use is to use workshops in conjunction with the
// training portal, which provides an OAuth provider endpoint for
// authentication.

function setup_oauth_credentials(metadata: any, client_id: string, client_secret: string) {
    var credentials = {
        client: {
            id: client_id,
            secret: client_secret
        },
        auth: {
            tokenHost: metadata["issuer"],
            authorizePath: metadata["authorization_endpoint"],
            tokenPath: metadata["token_endpoint"]
        },
        options: {
            authorizationMethod: "body",
        },
        http: {
            rejectUnauthorized: false
        }
    }

    return credentials
}

async function install_portal_auth(app: express.Application) {
    const issuer = PORTAL_URL

    const client_id: string = PORTAL_CLIENT_ID
    const client_secret: string = PORTAL_CLIENT_SECRET

    const metadata = {
        issuer: issuer,
        authorization_endpoint: issuer + "/oauth2/authorize/",
        token_endpoint: issuer + "/oauth2/token/"
    }

    logger.info("OAuth server metadata", { metadata: metadata })

    const credentials = setup_oauth_credentials(metadata, client_id,
        client_secret)

    logger.info("OAuth server credentials", { credentials: credentials })

    const oauth2 = require('simple-oauth2').create(credentials)

    register_oauth_callback(app, oauth2, verify_session_access)
    register_oauth_handshake(app, oauth2)
}

// Authentication via OAuth always has priority if configuration for HTTP
// basic authentication is also provided. Setting HTTP basic authentication
// password to "*" has side affect of disabling authentication. This is to
// cope with situation where wasn't possible to prevent the passing of any
// environment variables because of them being required parameters in a
// template.

export async function setup_access(app: express.Application) {
    if (PORTAL_CLIENT_ID) {
        logger.info("Install portal oauth support.")

        await install_portal_auth(app)
    }
    else if (AUTH_USERNAME) {
        if (AUTH_USERNAME != "*") {
            logger.info("Install HTTP Basic auth support.")

            await install_basic_auth(app)
        }
        else {
            logger.info("All authentication has been disabled.")
        }
    }
}
