import * as express from "express"
import { createProxyMiddleware } from "http-proxy-middleware"

import { config } from "./config"

// Setup intercepts for proxying to internal application ports.

export function setup_proxy(app: express.Application, auth: string) {
    if (config.ingresses) {
        // For each ingress, create a proxy to the internal application port,
        // Kubernetes service, or external host.

        for (let i = 0; i < config.ingresses.length; i++) {
            let ingress = config.ingresses[i]
            let name = ingress["name"]

            let secure = ingress["secure"]

            if (secure === undefined)
                secure = true

            let path_rewrite = ingress["pathRewrite"] || []

            let path_rewrite_map = {}
    
            for (let item of path_rewrite) {
                path_rewrite_map[item["pattern"]] = item["replacement"]
            }

            // For a specific ingress, we need to match a host name where the
            // session name is either prefixed or suffixed with the name of the
            // ingress. Note that suffix use is deprecated but need to support
            // it for backwards compatibility.

            let hosts = []

            hosts.push(`${name}-${config.session_name}.${config.ingress_domain}`)
            hosts.push(`${config.session_name}-${name}.${config.ingress_domain}`)

            // The filter/router function should only match and return a target
            // for requests that are actually for the calculated host names.

            function filter(pathname, req) {
                let host = req.headers.host

                if (!host)
                    return false

                if (hosts.includes(host)) {
                    // If the ingress has an authentication type, then we need
                    // to check that the request has the correct authentication
                    // type. Otherwise, we just need to check that the request
                    // is for the correct path.

                    let ingress_auth_type = ingress?.authentication?.type || "session"

                    if (ingress_auth_type != auth)
                        return false

                    let ingress_path = ingress?.path || "/"

                    if (ingress_path.endsWith("/")) {
                        return pathname.startsWith(ingress_path)
                    } else {
                        return pathname == ingress_path || pathname.startsWith(ingress_path + "/")
                    }
                }

                return false
            }

            function router(req) {
                let protocol = ingress["protocol"] || "http"
                let host = ingress["host"]
                let port = ingress["port"]

                if (!port || port == "0")
                    port = protocol == "https" ? 443 : 80

                return {
                    protocol: `${protocol}:`,
                    host: host || "localhost",
                    port: port
                }
            }

            app.use(createProxyMiddleware(filter, {
                target: "http://localhost",
                router: router,
                changeOrigin: ingress["changeOrigin"] === undefined ? true : ingress["changeOrigin"],
                pathRewrite: path_rewrite_map,
                secure: secure,
                ws: true,
                onProxyReq: (proxyReq, req, res) => {
                    let host = req.headers.host

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
                },
                onProxyReqWs: (proxyReq, req, socket, options, head) => {
                    let host = req.headers.host

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
}
