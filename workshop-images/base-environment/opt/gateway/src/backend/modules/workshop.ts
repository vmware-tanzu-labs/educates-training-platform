import * as path from "path"
import * as express from "express"
import axios from "axios"

import { createProxyMiddleware } from "http-proxy-middleware"

let axios_retry = require("axios-retry")

import { config } from "./config"

const URL_REGEX = new RegExp(/[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)?/gi)

export function setup_workshop(app: express.Application) {
    let workshop_url = config.workshop_url || '/workshop/'

    app.get('/workshop/.redirect-when-workshop-is-ready', function (req, res) {
        // If renderer is declared as being remote, in which case a workshop URL
        // should be provided which maps to a qualified http/https URL, assume
        // that is really externally hosted workshop content and perform an
        // immediate redirect to that site.

        if (config.workshop_renderer == "remote")
            return res.redirect(workshop_url)

        // In the case of having static workshop content, then also redirect.
        // In this case it should normally redirect to /workshop/ although
        // technically could redirect to a different sub URL path.

        if (config.workshop_renderer == "static")
            return res.redirect(workshop_url)

        // Finally, if workshop content renderer isn't enabled then redirect as
        // well. This should probably end up with an error when redirected.

        if (!config.enable_workshop)
            return res.redirect(workshop_url)

        // Check whether the internal workshop content renderer is ready.

        var client = axios.create({ baseURL: 'http://127.0.0.1:' + config.workshop_port })

        var options = {
            retries: 3,
            retryDelay: (retryCount) => {
                return retryCount * 500
            }
        };

        axios_retry(client, options)

        client.get('/workshop/')
            .then((result) => {
                res.redirect(workshop_url)
            })
            .catch((error) => {
                console.log('Error with workshop backend', error)
                res.redirect(workshop_url)
            })
    })

    app.get("/workshop$", (req, res) => {
        res.redirect("/workshop/")
    })

    if (config.workshop_renderer == "remote") {
        app.get("/workshop/$", (req, res) => {
            res.redirect(workshop_url)
        })
    }
    else if (config.workshop_renderer == "local" && config.workshop_renderer_type == "classic") {
        app.use(createProxyMiddleware("/workshop/", {
            target: 'http://127.0.0.1:' + config.workshop_port,
            ws: true,
        }))
    }
    else {
        // In the case of static workshop content the requirement is that it
        // be at a base URL with sub path of /workshop/content/ so redirect
        // to that. This is so there is no conflict with /workshop/static.

        app.get("/workshop/$", (req, res) => {
            res.redirect('/workshop/content/')
        })

        app.use("/workshop/content/", express.static(path.join(config.workshop_dir, "public")))
    }
}
