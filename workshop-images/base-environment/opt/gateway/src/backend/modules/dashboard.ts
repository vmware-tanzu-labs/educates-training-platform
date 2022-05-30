import * as express from "express"
import * as fs from "fs"
import * as path from "path"

import { send_analytics_event } from "./session"

const home_directory = require('os').homedir()

import { config } from "./config"

export function setup_dashboard(app: express.Application) {
    if (!config.enable_dashboard)
        return

    app.get("/dashboard/", async (req, res) => {
        if (!req.session.page_hits)
            req.session.page_hits = 1
        else
            req.session.page_hits++

        let locals = { "workshop_ready": true, "workshop_status": "", "time_started": req.session.started, "page_hits": req.session.page_hits }

        let setup_scripts_failed_file = path.join(home_directory, ".local", "share", "workshop", "setup-scripts.failed")

        if (fs.existsSync(setup_scripts_failed_file)) {
            locals["workshop_ready"] = false
            locals["workshop_status"] = "setup-scripts-failed"

            let data = { error: "setup-scripts-failed" }

            try {
                await send_analytics_event(req.session.token, "Workshop/Error", { data: data })
            } catch (err) {
                // Ignore any error as we don't want it prevent page loading.
            }
        }

        let download_workshop_failed_file = path.join(home_directory, ".local", "share", "workshop", "download-workshop.failed")

        if (fs.existsSync(download_workshop_failed_file)) {
            locals["workshop_ready"] = false
            locals["workshop_status"] = "download-workshop-failed"

            let data = { error: "download-workshop-failed" }

            try {
                await send_analytics_event(req.session.token, "Workshop/Error", { data: data })
            } catch (err) {
                // Ignore any error as we don't want it prevent page loading.
            }
        }

        locals["session_owner"] = ""
        locals["user_context"] = ""

        if (req.session.identity) {
            if (req.session.identity.owner)
                locals["session_owner"] = req.session.identity.owner

            if (req.session.identity.staff)
                locals["user_context"] = req.session.identity.user
        }

        res.render("dashboard-page", locals)
    })
}
