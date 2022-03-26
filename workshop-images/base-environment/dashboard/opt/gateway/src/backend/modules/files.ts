import * as express from "express"
import { createProxyMiddleware } from "http-proxy-middleware"

import { config } from "./config"

export function setup_files(app: express.Application) {
    if (!config.enable_files)
        return

    app.use("/files/", createProxyMiddleware({
        target: `http://127.0.0.1:${config.httpd_port}`
    }))
}
