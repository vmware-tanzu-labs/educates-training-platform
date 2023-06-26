import * as express from "express"

const axios = require("axios").default

import { logger } from "./logger"

const PORTAL_API_URL = process.env.PORTAL_API_URL

const SESSION_NAME = process.env.SESSION_NAME

async function get_session_schedule(session, oauth2_client) {
    let access_token = oauth2_client.createToken(JSON.parse(session.token))

    const options = {
        baseURL: PORTAL_API_URL,
        headers: { "Authorization": "Bearer " + access_token["token"]["access_token"] },
        responseType: "json"
    }

    const url = "/workshops/session/" + SESSION_NAME + "/schedule/"

    try {
        return (await axios.get(url, options)).data
    } catch (error) {
        logger.error("Error retrieving session schedule", { status: error.response.status, data: error.response.data })

        throw new Error("Error retrieving session schedule")
    }
}

async function get_extend_schedule(session, oauth2_client) {
    let access_token = oauth2_client.createToken(JSON.parse(session.token))

    const options = {
        baseURL: PORTAL_API_URL,
        headers: { "Authorization": "Bearer " + access_token["token"]["access_token"] },
        responseType: "json"
    }

    const url = "/workshops/session/" + SESSION_NAME + "/extend/"

    try {
        return (await axios.get(url, options)).data
    } catch (error) {
        logger.error("Error extending session duration", { status: error.response.status, data: error.response.data })

        throw new Error("Error extending session duration")
    }
}

export async function send_analytics_event(session, oauth2_client, event, data) {
    let access_token = oauth2_client.createToken(JSON.parse(session.token))

    const options = {
        baseURL: PORTAL_API_URL,
        headers: { "Authorization": "Bearer " + access_token["token"]["access_token"] },
        responseType: "json"
    }

    const url = "/workshops/session/" + SESSION_NAME + "/event/"

    let payload = { "event": {} }

    Object.assign(payload["event"], data, { "name": event })

    try {
        return (await axios.post(url, payload, options)).data
    } catch (error) {
        logger.error("Error reporting workshop event", error.response.status, error.response.data)

        throw new Error("Error reporting workshop event")
    }
}

export function setup_session(app: express.Application, oauth2_client: any) {
    app.get("/session/schedule", async (req, res) => {
        if (req.session.token) {
            try {
                let details = await get_session_schedule(req.session, oauth2_client)

                logger.info("Session schedule", details)

                return res.json(details)
            } catch (error) {
                return res.status(500).send(error.message)
            }
        }

        res.json({})
    })

    app.get("/session/extend", async (req, res) => {
        if (req.session.token) {
            try {
                let details = await get_extend_schedule(req.session, oauth2_client)

                logger.info("Extended schedule", details)

                return res.json(details)
            } catch (error) {
                return res.status(500).send(error.message)
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

                let details = await send_analytics_event(req.session, oauth2_client, event, data)

                return res.json(details)
            } catch (error) {
                return res.status(500).send(error.message)
            }
        }

        res.json({})
    })
}
