import * as express from "express"

const axios = require("axios").default

import { logger } from "../modules/logger"

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

module.exports = (app: express.Application, prefix: string): express.Router => {
    let router = express.Router()

    router.get("/schedule", async (req, res) => {
        if (req.session.token) {
            var details = await get_session_schedule(req.session.token)

            logger.info("Session schedule", details)

            return res.json(details)
        }

        res.json({})
    })

    router.get("/extend", async (req, res) => {
        if (req.session.token) {
            var details = await get_extend_schedule(req.session.token)

            logger.info("Extended schedule", details)

            return res.json(details)
        }

        res.json({})
    })

    return router
}