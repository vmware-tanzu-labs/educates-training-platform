import * as express from "express"
import * as path from "path"

import { config } from "./config"

export function setup_files(app: express.Application) {
    if (!config.enable_files)
        return

    app.use("/files", express.static(config.files_dir))
}