import * as express from "express"
import * as fs from "fs"

import { config } from "./config"

var enable_console = process.env.ENABLE_CONSOLE == "true"
var enable_dashboard = process.env.ENABLE_DASHBOARD == "true"
var enable_slides = process.env.ENABLE_SLIDES == "true"
var enable_terminal = process.env.ENABLE_TERMINAL == "true"

var google_tracking_id = process.env.GOOGLE_TRACKING_ID || ""

var workshop_name = process.env.WORKSHOP_NAME || ""
var session_namespace = process.env.SESSION_NAMESPACE || ""
var workshop_namespace = process.env.WORKSHOP_NAMESPACE || ""
var training_portal = process.env.TRAINING_PORTAL || ""
var ingress_domain = process.env.INGRESS_DOMAIN || ""
var ingress_protocol = process.env.INGRESS_PROTOCOL || "http"

var portal_api_url = process.env.PORTAL_API_URL || ""

var enable_portal = portal_api_url != ""

var enable_countdown = process.env.ENABLE_COUNTDOWN == "true"

export function setup_dashboard(app: express.Application) {
    if (!enable_dashboard)
        return

    app.get("/dashboard/", (req, res) => {
        if (!req.session.page_hits)
            req.session.page_hits = 1
        else
            req.session.page_hits++

        let locals = { "page_hits": req.session.page_hits }

        res.render("dashboard-page", locals)
    })
}