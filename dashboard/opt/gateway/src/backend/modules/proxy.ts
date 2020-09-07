import * as express from "express"
import * as matcher from "matcher"
import { createProxyMiddleware } from "http-proxy-middleware"

import { config } from "./config"

// Setup intercepts for proxying to internal application ports.

export function setup_proxy(app: express.Application) {
    function filter(pathname, req) {
        let host = req.headers.host

        if (!host)
            return false

        let node = host.split(".")[0]
        let ingresses = config.ingresses

        for (let i = 0; i < ingresses.length; i++) {
            let ingress = ingresses[i]
            if (node.endsWith("-" + ingress["name"]))
                return true
        }

        return false
    }

    function router(req) {
        let host = req.headers.host
        let node = host.split(".")[0]
        let ingresses = config.ingresses

        for (let i = 0; i < ingresses.length; i++) {
            let ingress = ingresses[i]
            if (node.endsWith("-" + ingress["name"])) {
                return {
                    protocol: "http:",
                    host: `${config.session_namespace}-${ingress.name}`,
                    port: ingress["port"],
                }
            }
        }
    }

    if (config.ingresses) {
        app.use(createProxyMiddleware(filter, {
            target: "http://localhost",
            router: router,
            ws: true,
            onProxyRes: (proxyRes, req, res) => {
                delete proxyRes.headers["x-frame-options"]
                delete proxyRes.headers["content-security-policy"]
                res.append("Access-Control-Allow-Origin", ["*"])
                res.append("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,HEAD")
                res.append("Access-Control-Allow-Headers", "Content-Type")
            },
            onError: (err, req, res) => {
                // The error handler can be called for either HTTP requests
                // or a web socket connection. Check whether have writeHead
                // method, indicating it is a HTTP request. Otherwise it is
                // actually a socket object and shouldn't do anything.

                if (res.writeHead)
                    res.status(503).render("proxy-error-page")
            }
        }))
    }
}
