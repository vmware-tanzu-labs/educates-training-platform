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

export async function send_analytics_event(access_token, event, data) {
    const options = {
        baseURL: PORTAL_API_URL,
        headers: { "Authorization": "Bearer " + access_token },
        responseType: "json"
    }

    const url = "/workshops/session/" + SESSION_NAME + "/event/"

    let payload = { "event": {} }

    Object.assign(payload["event"], data, { "name": event })

    return (await axios.post(url, payload, options)).data
}

export function setup_session(app: express.Application) {
    app.get("/session/schedule", async (req, res) => {
        if (req.session.token) {
            try {
                let details = await get_session_schedule(req.session.token)

                logger.info("Session schedule", details)

                return res.json(details)
            } catch (error) {
                logger.error("Error retrieving session schedule", error)

                return res.status(500).send("Error retrieving session schedule")
            }
        }

        res.json({})
    })

    app.get("/session/extend", async (req, res) => {
        if (req.session.token) {
            try {
                let details = await get_extend_schedule(req.session.token)

                logger.info("Extended schedule", details)

                return res.json(details)
            } catch (error) {
                logger.error("Error extending session duration", error)

                return res.status(500).send("Error extending session duration")
            }
        }

        res.json({})
    })

    app.use("/session/event", express.json())

    app.post("/session/event", async (req, res) => {
        if (req.session.token) {
            try {
                let payload = req.body

                let data = payload["event"]
                let event = data["name"]

                logger.info("Forwarding event", payload)

                delete data["name"]

                let details = await send_analytics_event(req.session.token, event, data)

                return res.json(details)
            } catch (error) {
                logger.error("Error reporting workshop event", error)

                return res.status(500).send("Error reporting workshop event")
            }
        }

        res.json({})
    })
}
