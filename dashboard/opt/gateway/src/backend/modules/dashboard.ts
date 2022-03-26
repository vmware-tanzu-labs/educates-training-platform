import * as express from "express"
import * as fs from "fs"
import * as path from "path"

const home_directory = require('os').homedir()

import { config } from "./config"

export function setup_dashboard(app: express.Application) {
    if (!config.enable_dashboard)
        return

    app.get("/dashboard/", (req, res) => {
        if (!req.session.page_hits)
            req.session.page_hits = 1
        else
            req.session.page_hits++

        let locals = { "workshop_ready": true, "workshop_status": "", "page_hits": req.session.page_hits }

        let setup_scripts_failed_file = path.join(home_directory, ".eduk8s", "setup-scripts.failed")

        if (fs.existsSync(setup_scripts_failed_file)) {
            locals["workshop_ready"] = false
            locals["workshop_status"] = "setup-scripts-failed"
        }

        let download_workshop_failed_file = path.join(home_directory, ".eduk8s", "download-workshop.failed")

        if (fs.existsSync(download_workshop_failed_file)) {
            locals["workshop_ready"] = false
            locals["workshop_status"] = "download-workshop-failed"
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
