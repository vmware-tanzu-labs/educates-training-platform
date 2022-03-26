import * as express from "express"
import axios from "axios"

import { createProxyMiddleware } from "http-proxy-middleware"

let axios_retry = require("axios-retry")

import { config } from "./config"

const URL_REGEX = new RegExp(/[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)?/gi)

export function setup_workshop(app: express.Application) {
    let workshop_url = config.workshop_url || '/workshop/'
    let is_external_workshop_url = config.workshop_url.match(URL_REGEX)

    app.get('/workshop/.redirect-when-workshop-is-ready', function (req, res) {
        // If a workshop URL is provided which maps to a qualified http/https
        // URL, assume that is externally hosted workshop content and perform
        // an immediate redirect to that site.

        if (is_external_workshop_url)
            return res.redirect(config.workshop_url)

        // If workshop content renderer isn't enabled then redirect as well.

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

    if (is_external_workshop_url) {
        app.get("/workshop/$", (req, res) => {
            res.redirect(workshop_url)
        })
    }
    else {
        app.use(createProxyMiddleware("/workshop/", {
            target: 'http://127.0.0.1:' + config.workshop_port,
        }))
    }
}
