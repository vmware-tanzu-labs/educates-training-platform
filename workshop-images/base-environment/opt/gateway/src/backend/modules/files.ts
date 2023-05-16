import * as express from "express"
import * as path from "path"

import { config } from "./config"

export function setup_files(app: express.Application, token: string=null) {
    if (!config.enable_files)
        return

    let handler = express.static(config.files_dir)

    if (token) {
        app.use("/files", async function (req, res, next) {
            let request_token = req.query.token
    
            if (!request_token || request_token != token)
                return next()

            return await handler(req, res, next)
        })
    }
    else {
        app.use("/files", handler)
    }
}
