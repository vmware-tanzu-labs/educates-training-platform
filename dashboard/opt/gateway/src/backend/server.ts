import * as express from "express"
import * as http from "http"
import * as path from "path"
import * as WebSocket from "ws"
import * as cors from "cors"
import * as session from "express-session"
import { v4 as uuidv4 } from "uuid"
import { createProxyMiddleware } from "http-proxy-middleware"

import { setup_authentication } from "./modules/authentication"
import { setup_proxy } from "./modules/proxy"
import { setup_terminals,TerminalServer } from "./modules/terminals"
import { setup_assets } from "./modules/assets"
import { setup_routing } from "./modules/routing"

const BASEDIR = path.dirname(path.dirname(__dirname))

const GATEWAY_PORT = 10080
const WEBDAV_PORT = 10084

const app = express()

const server = http.createServer(app)

const terminals = new TerminalServer()

app.set("views", path.join(BASEDIR, "src/backend/views"))
app.set("view engine", "pug")

app.use(cors())

// When running in Kubernetes we are always behind a proxy, so trust headers.

app.set("trust proxy", true)

// Helpers for determining the idle state of the workshop session. This is
// deliberately added up front so that it isn't gated by authentication.

let last_accessed: number = (new Date()).getTime()

app.get("/session/poll", (req, res) => {
    last_accessed = (new Date()).getTime()
    res.json({})
})

app.get("/session/activity", (req, res) => {
    const idle_time = ((new Date()).getTime() - last_accessed) / 1000.0
    res.json({ "idle-time": idle_time })
})

// Short circuit WebDAV access as it handles its own authentication.

const ENABLE_WEBDAV = process.env.ENABLE_WEBDAV

if (ENABLE_WEBDAV == "true") {
    app.use("/webdav/", createProxyMiddleware({
        target: `http://127.0.0.1:${WEBDAV_PORT}`,
        ws: true
    }))
}

// Enable use of a client side session cookie for the user. This is used to
// track whether the user has logged in when using OAuth. Session will expire
// after 24 hours. When we know we are being embedded in an iframe, we need
// to allow cookie to be used cross site, but in doing that, force use of a
// secure cookie. If the ingress protocol wasn"t actually "http", this means
// that access to the workshop session will be blocked.

const INGRESS_PROTOCOL = process.env.INGRESS_PROTOCOL || "http"
const FRAME_ANCESTORS = process.env.FRAME_ANCESTORS

let cookie_options: express.CookieOptions = {
    path: "/",
    secure: false,
    sameSite: "lax",
    maxAge: 24 * 60 * 60 * 1000
}

if (INGRESS_PROTOCOL == "https")
    cookie_options["secure"] = true

if (FRAME_ANCESTORS) {
    cookie_options["sameSite"] = "none"
    cookie_options["secure"] = true
}

app.use(session({
    name: "workshop-session-id",
    genid: (req) => { return uuidv4() },
    secret: uuidv4(),
    cookie: cookie_options,
    resave: false,
    saveUninitialized: true,
}))

function setup_signals() {
    process.on("SIGTERM", () => {
        console.log("Starting shutdown.")
        console.log("Closing HTTP server.")

        terminals.close_all_sessions()

        server.close(() => {
            console.log("HTTP server closed.")
            process.exit(0)
        })
    })
}

function start_http_server() {
    server.listen(GATEWAY_PORT, () => {
        console.log(`HTTP server running on port ${GATEWAY_PORT}.`)
    })
}

// Setup everything and start listener. Because setup of OAuth authentication
// requires some calls to be made back to the port web application, this needs
// to be done within an async function.

async function main() {
    try {
        setup_signals()

        await setup_authentication(app)

        setup_proxy(app)
        setup_terminals(app, server)
        setup_assets(app)
        setup_routing(app)
        
        start_http_server()
    } catch (error) {
        console.log("Unexpected error occurred", error)
    }
}

main()