import * as express from "express"
import * as path from "path"
import * as WebSocket from "ws"
import * as cors from "cors"
import * as session from "express-session"
import { v4 as uuidv4 } from "uuid"

import { TerminalServer } from "./modules/terminals"

const BASEDIR = path.dirname(path.dirname(__dirname))

const GATEWAY_PORT = 10080

const app = express()

app.set("views", path.join(BASEDIR, "src/backend/views"))
app.set("view engine", "pug")

app.use(cors())

// When running in Kubernetes we are always behind a proxy, so trust headers.

app.set("trust proxy", true)

// Helpers for determining the idle state of the workshop session. This is
// deliberately added up front so that it isn't gated by authentication.

let last_accessed: number = (new Date()).getTime()

app.get("/status/beacon.png", (req, res) => {
    last_accessed = (new Date()).getTime()
    res.sendFile(path.join(BASEDIR, "src/frontend/images/beacon.png"))
})

app.get("/session/poll", (req, res) => {
    last_accessed = (new Date()).getTime()
    res.json({})
})

app.get("/session/activity", (req, res) => {
    const idle_time = ((new Date()).getTime() - last_accessed) / 1000.0
    res.json({ 'idle-time': idle_time})
})

// Enable use of a client side session cookie for the user. This is used to
// track whether the user has logged in when using OAuth. Session will expire
// after 24 hours. When we know we are being embedded in an iframe, we need
// to allow cookie to be used cross site, but in doing that, force use of a
// secure cookie. If the ingress protocol wasn't actually "http", this means
// that access to the workshop session will be blocked.

const INGRESS_PROTOCOL = process.env.INGRESS_PROTOCOL || "http"
const FRAME_ANCESTORS = process.env.FRAME_ANCESTORS

let cookie_options: express.CookieOptions = {
    path: "/",
    secure: false,
    sameSite: 'lax',
    maxAge: 24*60*60*1000
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

app.use("/static/images", express.static(path.join(BASEDIR, "src/frontend/images")))
app.use("/static/styles", express.static(path.join(BASEDIR, "src/frontend/styles")))
app.use("/static/scripts", express.static(path.join(BASEDIR, "build/frontend/scripts")))

app.use("/static/styles", express.static(path.join(BASEDIR, "node_modules/xterm/css")))
app.use("/static/styles", express.static(path.join(BASEDIR, "node_modules/bootstrap/dist/css")))

app.use("/static/fonts", express.static(path.join(BASEDIR, "fonts/SourceCodePro"), { maxAge: 3600000 }))

app.get("/", (req, res) => {
    res.redirect("/terminal/session/1")
})

app.get("/terminal/testing/", (req, res) => {
    res.render("testing/dashboard", { endpoint_id: terminals.id })
})

app.get("/terminal/session/:session_id", (req, res) => {
    let session_id = req.params.session_id || "1"

    res.render("terminal", { endpoint_id: terminals.id, session_id: session_id })
})

let server = app.listen(GATEWAY_PORT, () => {
    console.log(`HTTP server running on port ${GATEWAY_PORT}.`)
})

let terminals = new TerminalServer(server)

process.on('SIGTERM', () => {
    console.log('Starting shutdown.')
    console.log('Closing HTTP server.')

    terminals.close_all_sessions()

    server.close(() => {
        console.log('HTTP server closed.')
        process.exit(0)
    })
})