import * as express from "express"

const axios = require("axios").default

import { logger } from "./logger"

const PORTAL_API_URL = process.env.PORTAL_API_URL

const SESSION_NAME = process.env.SESSION_NAME

async function get_session_schedule(access_token) {
    const options = {
        baseURL: PORTAL_API_URL,
        headers: { "Authorization": "Bearer " + access_token },
        responseType: "json"
    }

    const url = "/workshops/session/" + SESSION_NAME + "/schedule/"

    return (await axios.get(url, options)).data
}

async function get_extend_schedule(access_token) {
    const options = {
        baseURL: PORTAL_API_URL,
        headers: { "Authorization": "Bearer " + access_token },
        responseType: "json"
    }

    const url = "/workshops/session/" + SESSION_NAME + "/extend/"

    return (await axios.get(url, options)).data
}

export function setup_session(app: express.Application) {
    app.get("/session/schedule", async (req, res) => {
        if (req.session.token) {
            let details = await get_session_schedule(req.session.token)

            logger.info("Session schedule", details)

            return res.json(details)
        }

        res.json({})
    })

    app.get("/session/extend", async (req, res) => {
        if (req.session.token) {
            let details = await get_extend_schedule(req.session.token)

            logger.info("Extended schedule", details)

            return res.json(details)
        }

        res.json({})
    })
}