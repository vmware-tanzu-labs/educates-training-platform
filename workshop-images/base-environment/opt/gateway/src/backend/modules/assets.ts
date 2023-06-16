import * as express from "express"
import * as path from "path"
import * as fs from "fs"

const BASEDIR = path.dirname(path.dirname(path.dirname(__dirname)))

export function setup_assets(app: express.Application) {
    app.use("/static/images", express.static(path.join(BASEDIR, "src/frontend/images")))
    app.use("/static/styles", express.static(path.join(BASEDIR, "src/frontend/styles")))
    app.use("/static/scripts", express.static(path.join(BASEDIR, "build/frontend/scripts")))

    if (fs.existsSync("/opt/eduk8s/theme") && fs.lstatSync("/opt/eduk8s/theme").isDirectory()) {
        app.use("/static/theme", express.static("/opt/eduk8s/theme"))
    }

    app.use("/static/webfonts", express.static(path.join(BASEDIR, "webfonts/SourceCodePro"), { maxAge: 3600000 }))

    app.use("/static/xterm/css", express.static(path.join(BASEDIR, "node_modules/xterm/css")))
    app.use("/static/bootstrap/css", express.static(path.join(BASEDIR, "node_modules/bootstrap/dist/css")))

    app.use("/static/fontawesome", express.static(path.join(BASEDIR, "node_modules/@fortawesome/fontawesome-free")))

    app.use("/static", express.static(path.join(BASEDIR, "node_modules/qrcode/build")))

    // The following implement a bypass for static assets of the workshop
    // renderer. This is done so accessible without authentication to satsify
    // the requirements of Microsoft Clarity to be able to access stylesheets.

    app.use("/workshop/static/images", express.static(path.join(BASEDIR, "../renderer", "src/frontend/images")))
    app.use("/workshop/static/styles", express.static(path.join(BASEDIR, "../renderer", "src/frontend/styles")))
    app.use("/workshop/static/scripts", express.static(path.join(BASEDIR, "../renderer", "build/frontend/scripts")))

    if (fs.existsSync("/opt/eduk8s/theme") && fs.lstatSync("/opt/eduk8s/theme").isDirectory()) {
        app.use("/workshop/static/theme", express.static("/opt/eduk8s/theme"))
    }

    app.use("/workshop/static/bootstrap/css", express.static(path.join(BASEDIR, "../renderer", "node_modules/bootstrap/dist/css")))
    app.use("/workshop/static/fontawesome", express.static(path.join(BASEDIR, "../renderer", "node_modules/@fortawesome/fontawesome-free")))
    app.use("/workshop/static/asciidoctor/css", express.static(path.join(BASEDIR, "../renderer", "node_modules/@asciidoctor/core/dist/css")))
    app.use("/workshop/static/highlight.js/styles", express.static(path.join(BASEDIR, "../renderer", "node_modules/highlight.js/styles")))
}
