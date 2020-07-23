import * as express from "express"

import { TerminalServer } from "../modules/terminals"

const ENABLE_TERMINAL = process.env.ENABLE_TERMINAL

const terminals = new TerminalServer()

module.exports = (app: express.Application, prefix: string): express.Router => {
    let router = express.Router()

    if (ENABLE_TERMINAL != "true")
        return router

    router.get("^/?$", (req, res) => {
        res.redirect(req.baseUrl + "/session/1")
    })

    router.get("/testing/", (req, res) => {
        res.render("testing/dashboard", { endpoint_id: terminals.id })
    })
    
    router.get("/session/:session_id", (req, res) => {
        let session_id = req.params.session_id || "1"
    
        res.render("terminal", { endpoint_id: terminals.id, session_id: session_id })
    })

    return router
}