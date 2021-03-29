import * as express from "express"
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
                let protocol = ingress["protocol"] || "http"
                let host = ingress["host"]
                let port = ingress["port"]

                if (!host) {
                    // XXX For backwards compatibility with old version of
                    // operator, for now still direct request to localhost
                    // when it is the console or editor. Later may expect
                    // host aliases to always exist even for those when using
                    // the operator on Kubernetes.

                    if (process.env.KUBERNETES_SERVICE_HOST && (
                        ingress["name"] == "console" ||
                        ingress["name"] == "editor")) {
                        host = "localhost"
                    }
                    else
                        host = `${config.session_namespace}-${ingress.name}`
                }

                if (!port || port == "0")
                    port = protocol == "https" ? 443 : 80

                return {
                    protocol: `${protocol}:`,
                    host: host,
                    port: port
                }
            }
        }
    }

    if (config.ingresses) {
        app.use(createProxyMiddleware(filter, {
            target: "http://localhost",
            router: router,
            changeOrigin: true,
            ws: true,
            onProxyReq: (proxyReq, req, res) => {
                let host = req.headers.host
                let node = host.split(".")[0]
                let ingresses = config.ingresses

                for (let i = 0; i < ingresses.length; i++) {
                    let ingress = ingresses[i]
                    if (node.endsWith("-" + ingress["name"])) {
                        if (ingress["headers"]) {
                            for (let j = 0; j < ingress["headers"].length; j++) {
                                let header = ingress["headers"][j]
                                let name = header["name"]
                                let value = header["value"] || ""
                                value = value.split("$(kubernetes_token)").join(config.kubernetes_token || "")
                                proxyReq.setHeader(name, value)
                            }
                        }
                    }
                }
            },
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
