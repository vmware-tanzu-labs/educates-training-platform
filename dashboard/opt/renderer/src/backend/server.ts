import * as express from "express"
import * as path from "path"
import * as morgan from "morgan"
import { Liquid } from "liquidjs"

import { logger } from "./modules/logger"
import { config, initialize_workshop } from "./modules/config"

const BASEDIR = path.dirname(path.dirname(__dirname))

// Read in global configuation.

let initialization_error: any

try {
    initialize_workshop()
}
catch (error) {
    initialization_error = error
}

// Setup the root for the application.

let app = express()

app.enable("strict routing")

// Add logging for inbound request.

app.use(morgan(config.log_format))

// Setup template rendering engine.

const engine = new Liquid()

// app.engine("liquid", engine.express())
app.set('views', path.join(BASEDIR, "src/backend/views/"))
app.set("view engine", "pug")

// Set up error page for all requests if workshop initialization failed.

if (initialization_error) {
    logger.error("Error initializing workshop", { err: initialization_error })

    app.use(function (req, res, next) {
        next(initialization_error)
    })
}

// Setup handlers for routes.

import { router } from "./modules/routes"

app.use(router)

// In OpenShift we are always behind a proxy, so trust the headers sent.

app.set("trust proxy", true)

// Start the application listener.

logger.info("Starting listener", { port: config.server_port })

let server = app.listen(config.server_port)

function handle_shutdown() {
    logger.info("Starting shutdown.")
    logger.info("Closing HTTP server.")
    server.close(function () {
        logger.info("HTTP server closed.")
        process.exit(0)
    })
}

process.on("SIGTERM", handle_shutdown)
process.on("SIGINT", handle_shutdown)
