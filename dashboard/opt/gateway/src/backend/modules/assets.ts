import * as express from "express"
import * as path from "path"
import * as fs from "fs"

const BASEDIR = path.dirname(path.dirname(path.dirname(__dirname)))

export function setup_assets(app: express.Application) {
    app.use("/static/images", express.static(path.join(BASEDIR, "src/frontend/images")))
    app.use("/static/styles", express.static(path.join(BASEDIR, "src/frontend/styles")))
    app.use("/static/scripts", express.static(path.join(BASEDIR, "build/frontend/scripts")))

    if (fs.existsSync("/opt/eduk8s/config/theme-dashboard.css")) {
        app.get("/static/styles/eduk8s-theme.css", (req, res) => {
            res.sendFile("/opt/eduk8s/config/theme-dashboard.css")
        })
    }
    else {
        app.get("/static/styles/eduk8s-theme.css", (req, res) => {
            res.setHeader('content-type', 'text/css')
            res.send("")
        })
    }

    if (fs.existsSync("/opt/eduk8s/config/theme-dashboard.js")) {
        app.get("/static/scripts/eduk8s-theme.js", (req, res) => {
            res.sendFile("/opt/eduk8s/config/theme-dashboard.js")
        })
    }
    else {
        app.get("/static/scripts/eduk8s-theme.js", (req, res) => {
            res.setHeader('content-type', 'text/javascript')
            res.send("")
        })
    }

    app.use("/static/webfonts", express.static(path.join(BASEDIR, "webfonts/SourceCodePro"), { maxAge: 3600000 }))

    app.use("/static/xterm/css", express.static(path.join(BASEDIR, "node_modules/xterm/css")))
    app.use("/static/bootstrap/css", express.static(path.join(BASEDIR, "node_modules/bootstrap/dist/css")))

    app.use("/static/fontawesome", express.static(path.join(BASEDIR, "node_modules/@fortawesome/fontawesome-free")))
}
