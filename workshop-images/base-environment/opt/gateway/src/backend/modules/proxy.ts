import * as express from "express"
import { createProxyMiddleware } from "http-proxy-middleware"

import { config } from "./config"

// Setup intercepts for proxying to internal application ports.

export function setup_proxy(app: express.Application, auth: string) {
    function filter(pathname, req) {
        let host = req.headers.host

        if (!host)
            return false

        let node = host.split(".")[0]
        let ingresses = config.ingresses

        for (let i = 0; i < ingresses.length; i++) {
            let ingress = ingresses[i]
            // Note that suffix use is deprecated, use prefix instead.
            if (node.startsWith(ingress["name"] + "-") || node.endsWith("-" + ingress["name"])) {
                let ingress_auth_type = ingress?.authentication?.type || "session"
                if (ingress_auth_type != auth)
                    return false
                return true
            }
        }

        return false
    }

    function router(req) {
        let host = req.headers.host
        let node = host.split(".")[0]
        let ingresses = config.ingresses

        for (let i = 0; i < ingresses.length; i++) {
            let ingress = ingresses[i]
            // Note that suffix use is deprecated, use prefix instead.
            if (node.startsWith(ingress["name"] + "-") || node.endsWith("-" + ingress["name"])) {
                let protocol = ingress["protocol"] || "http"
                let host = ingress["host"]
                let port = ingress["port"]

                // Replaced this with forwarding to localhost below.
                //
                // if (!host)
                //     host = `${ingress.name}-${config.session_namespace}`

                if (!port || port == "0")
                    port = protocol == "https" ? 443 : 80

                return {
                    protocol: `${protocol}:`,
                    host: host || "localhost",
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
                    // Note that suffix use is deprecated, use prefix instead.
                    if (node.startsWith(ingress["name"] + "-") || node.endsWith("-" + ingress["name"])) {
                        if (ingress["headers"]) {
                            for (let j = 0; j < ingress["headers"].length; j++) {
                                let header = ingress["headers"][j]
                                let name = header["name"]
                                let value = header["value"] || ""
                                value = value.split("$(kubernetes_token)").join(config.kubernetes_token || "")
                                proxyReq.setHeader(name, value)
                            }
                        }
                        let target_host = ingress["host"] || "localhost"
                        if (target_host == "localhost")
                            proxyReq.setHeader("host", host)
                    }
                }
            },
            onProxyReqWs: (proxyReq, req, socket, options, head) => {
                let host = req.headers.host
                let node = host.split(".")[0]
                let ingresses = config.ingresses

                for (let i = 0; i < ingresses.length; i++) {
                    let ingress = ingresses[i]
                    // Note that suffix use is deprecated, use prefix instead.
                    if (node.startsWith(ingress["name"] + "-") || node.endsWith("-" + ingress["name"])) {
                        if (ingress["headers"]) {
                            for (let j = 0; j < ingress["headers"].length; j++) {
                                let header = ingress["headers"][j]
                                let name = header["name"]
                                let value = header["value"] || ""
                                value = value.split("$(kubernetes_token)").join(config.kubernetes_token || "")
                                proxyReq.setHeader(name, value)
                            }
                        }
                        let target_host = ingress["host"] || "localhost"
                        if (target_host == "localhost")
                            proxyReq.setHeader("host", host)
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

                console.log("Proxy", err)

                if (res.writeHead)
                    res.status(503).render("proxy-error-page")
            }
        }))
    }
}
