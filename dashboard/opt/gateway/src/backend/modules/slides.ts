import * as express from "express"

import { config } from "./config"

export function setup_slides(app: express.Application) {
    if (!config.enable_slides || !config.slides_dir)
        return

    app.use("/slides", express.static(config.slides_dir))
    app.use("/slides", express.static("/opt/revealjs"))
}
