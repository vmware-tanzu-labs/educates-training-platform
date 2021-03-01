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

        let locals = { "workshop_ready": true, "page_hits": req.session.page_hits }

        let download_workshop_err_file = path.join(home_directory, ".eduk8s", "download-url.failed")

        if (fs.existsSync(download_workshop_err_file))
            locals["workshop_ready"] = false

        res.render("dashboard-page", locals)
    })
}
