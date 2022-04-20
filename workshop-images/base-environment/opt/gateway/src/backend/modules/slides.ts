import * as express from "express"
import * as glob from "glob"
import * as semver from "semver"

import { config } from "./config"

export function setup_slides(app: express.Application) {
    if (!config.enable_slides || !config.slides_dir)
        return

    app.use("/slides", express.static(config.slides_dir))

    let workshop_spec = config.workshop["spec"] || {}
    let session = workshop_spec["session"] || {}
    let applications = session["applications"] || {}
    let slides = applications["slides"] || {}

    let revealjs = slides["reveal.js"] || {}
    let impressjs = slides["impress.js"] || {}

    let revealjs_version = revealjs["version"]
    let impressjs_version = impressjs["version"]

    if (revealjs_version) {
        console.log(`Requested reveal.js version ${revealjs_version}.`)
        let versions = glob.sync("*", { cwd: "/opt/slides/reveal.js" })
        let matched = semver.maxSatisfying(versions, revealjs_version)
        console.log(`Matched reveal.js version ${matched}.`)
        if (matched)
            app.use("/slides", express.static(`/opt/slides/reveal.js/${matched}`))
    }
    else if (impressjs_version) {
        console.log(`Requested impress.js version ${impressjs_version}.`)
        let versions = glob.sync("*", { cwd: "/opt/slides/impress.js" })
        let matched = semver.maxSatisfying(versions, impressjs_version)
        console.log(`Matched impress.js version ${matched}.`)
        if (matched)
            app.use("/slides", express.static(`/opt/slides/impress.js/${matched}`))
    }
}
