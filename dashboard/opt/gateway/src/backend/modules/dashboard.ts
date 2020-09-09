import * as express from "express"

import { config } from "./config"

export function setup_dashboard(app: express.Application) {
    if (!config.enable_dashboard)
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
