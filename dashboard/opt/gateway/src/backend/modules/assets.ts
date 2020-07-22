import * as express from "express"
import * as path from "path"

const BASEDIR = path.dirname(path.dirname(path.dirname(__dirname)))

export function setup_assets(app: express.Application) {
    app.use("/static/images", express.static(path.join(BASEDIR, "src/frontend/images")))
    app.use("/static/styles", express.static(path.join(BASEDIR, "src/frontend/styles")))
    app.use("/static/scripts", express.static(path.join(BASEDIR, "build/frontend/scripts")))

    app.use("/static/styles", express.static(path.join(BASEDIR, "node_modules/xterm/css")))
    app.use("/static/styles", express.static(path.join(BASEDIR, "node_modules/bootstrap/dist/css")))

    app.use("/static/fonts", express.static(path.join(BASEDIR, "fonts/SourceCodePro"), { maxAge: 3600000 }))
}