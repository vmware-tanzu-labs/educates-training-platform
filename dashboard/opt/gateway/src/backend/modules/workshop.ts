import * as express from "express"
import axios from "axios"

import { createProxyMiddleware } from "http-proxy-middleware"

let axios_retry = require("axios-retry")

export function setup_workshop(app: express.Application) {
    app.get('/workshop/.redirect-when-workshop-is-ready', function (req, res) {
        var client = axios.create({ baseURL: 'http://127.0.0.1:10082' })

        var options = {
            retries: 3,
            retryDelay: (retryCount) => {
                return retryCount * 500
            }
        };

        axios_retry(client, options)

        client.get('/workshop/')
            .then((result) => {
                res.redirect('/workshop/')
            })
            .catch((error) => {
                console.log('Error with workshop backend', error)
                res.redirect('/workshop/')
            })
    })

    app.use(createProxyMiddleware("/workshop/", {
        target: 'http://127.0.0.1:10082',
    }))
}