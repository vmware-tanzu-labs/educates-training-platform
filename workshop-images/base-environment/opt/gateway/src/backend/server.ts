import * as express from "express"
import * as http from "http"
import * as path from "path"
import * as WebSocket from "ws"
import * as cors from "cors"
import * as session from "express-session"
import { v4 as uuidv4 } from "uuid"
import { createProxyMiddleware } from "http-proxy-middleware"
import * as morgan from "morgan"
import * as url from "url"

import { setup_access } from "./modules/access"
import { setup_proxy } from "./modules/proxy"
import { setup_session } from "./modules/session"
import { setup_terminals, terminals } from "./modules/terminals"
import { setup_messages, messages } from "./modules/messages"
import { setup_dashboard } from "./modules/dashboard"
import { setup_assets } from "./modules/assets"
import { setup_slides } from "./modules/slides"
import { setup_examiner } from "./modules/examiner"
import { setup_workshop, setup_workshop_config } from "./modules/workshop"
import { setup_files } from "./modules/files"
import { setup_uploads } from "./modules/uploads"
import { setup_routing } from "./modules/routing"

import { logger } from "./modules/logger"
import { config } from "./modules/config"

const BASEDIR = path.dirname(path.dirname(__dirname))

const GATEWAY_PORT = parseInt(process.env.GATEWAY_PORT || "10081")

const app = express()

const server = http.createServer(app)

app.set("views", path.join(BASEDIR, "src/backend/views"))
app.set("view engine", "pug")

app.locals.config = config

app.use("*", cors())

// Add logging for request.

const LOG_FORMAT = process.env.LOG_FORMAT || 'dev'

app.use(morgan(LOG_FORMAT))

// When running in Kubernetes we are always behind a proxy, so trust headers.

app.set("trust proxy", true)

// Helpers for determining the idle state of the workshop session. This is
// deliberately added up front so that it isn't gated by authentication.

let last_accessed: number = (new Date()).getTime()
let last_exposed: number = (new Date()).getTime()

app.get("/session/poll", (req, res) => {
    last_accessed = (new Date()).getTime()

    const hidden = req.query.hidden

    if (hidden != "true") {
        last_exposed = last_accessed
    }

    res.json({})
})

app.get("/session/activity", (req, res) => {
    const idle_time = ((new Date()).getTime() - last_accessed) / 1000.0
    const last_view = ((new Date()).getTime() - last_exposed) / 1000.0
    res.json({ "idle-time": idle_time, "last-view": last_view })
})

// Short circuit WebDAV access as it handles its own authentication.

const ENABLE_WEBDAV = process.env.ENABLE_WEBDAV

if (ENABLE_WEBDAV == "true") {
    app.use("/webdav/", createProxyMiddleware({
        target: `http://127.0.0.1:${config.webdav_port}`,
        ws: true
    }))
}

// Setup proxies for ingresses where authentication is disabled.

setup_proxy(app, "none")

// Enable use of a client side session cookie for the user. This is used to
// track whether the user has logged in when using OAuth. Session will expire
// after 24 hours. When we know we are being embedded in an iframe, we need
// to allow cookie to be used cross site, but in doing that, force use of a
// secure cookie. If the ingress protocol wasn't actually "http", this means
// that access to the workshop session will be blocked.

const ENVIRONMENT_NAME = process.env.ENVIRONMENT_NAME || "workshop"

const FRAME_ANCESTORS = process.env.FRAME_ANCESTORS

const SESSION_COOKIE_DOMAIN = process.env.SESSION_COOKIE_DOMAIN || null

var cookie_name = "workshop-session-id"

if (SESSION_COOKIE_DOMAIN) {
    cookie_name = `sessionid-${ENVIRONMENT_NAME}`
}

let cookie_options: express.CookieOptions = {
    path: "/",
    domain: SESSION_COOKIE_DOMAIN,
    secure: false,
    sameSite: "lax",
    maxAge: 24 * 60 * 60 * 1000
}

if (FRAME_ANCESTORS) {
    cookie_options["sameSite"] = "none"
    cookie_options["secure"] = true
}

app.use(session({
    name: cookie_name,
    genid: (req) => { return uuidv4() },
    secret: uuidv4(),
    cookie: cookie_options,
    resave: false,
    saveUninitialized: true,
}))

function setup_signals() {
    process.on("SIGTERM", () => {
        logger.info("Starting shutdown.")
        logger.info("Closing HTTP server.")

        terminals.close_all_sessions()

        server.close(() => {
            logger.info("HTTP server closed.")
            process.exit(0)
        })
    })
}

function start_http_server() {
    server.listen(GATEWAY_PORT, () => {
        logger.info(`HTTP server running on port ${GATEWAY_PORT}.`)
    })
}

// Setup everything and start listener. Because setup of OAuth authentication
// requires some calls to be made back to the port web application, this needs
// to be done within an async function.

async function main() {
    try {
        let oauth2_client: any

        setup_signals()

        setup_workshop_config(app, config.config_password)

        setup_examiner(app, config.services_password)
        setup_files(app, config.services_password)
        setup_uploads(app, config.services_password)

        setup_messages(app, server, config.services_password)

        // Assets are made visible without authentication so that Microsoft
        // Clarity can access any stylesheets so it can render screen
        // recordings. Note that this includes a bypass for the workshop
        // renderer static assets as otherwise we would only proxy to the
        // workshop renderer as a whole behind authentication.

        setup_assets(app)

        oauth2_client = await setup_access(app)

        setup_proxy(app, "session")

        setup_session(app, oauth2_client)

        setup_workshop_config(app)

        setup_terminals(app, server)
        setup_workshop(app)
        setup_slides(app)
        setup_examiner(app)
        setup_files(app)
        setup_uploads(app)

        setup_messages(app, server)

        setup_dashboard(app, oauth2_client)

        setup_routing(app)

        server.on("upgrade", (req, socket, head) => {
            let parsedUrl = url.parse(req.url, true)
            if (terminals.is_enabled() && parsedUrl.pathname == "/terminal/server") {
                terminals.session_manager().handle_upgrade(req, socket, head)
            } else if (terminals.is_enabled() && parsedUrl.pathname == "/message/server") {
                messages.session_manager().handle_upgrade(req, socket, head)
            }
        })

        start_http_server()
    } catch (error) {
        logger.error("Unexpected error occurred", error)
    }
}

main()
