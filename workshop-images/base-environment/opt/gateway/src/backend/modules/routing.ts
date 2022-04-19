import * as express from "express"
import * as path from "path"
import * as glob from "glob"

const BASEDIR = path.dirname(path.dirname(path.dirname(__dirname)))

// Set the default page for the site and install any routes. Note that any extra
// packages and the workshop take precedence so if they install routes or an
// index page that conflicts it will break the operation of the dashboard.

export function setup_routing(app: express.Application) {
    let routes_directories = []

    // Work out set of directories which can hold routes and index file.

    routes_directories.push(path.join(BASEDIR, "build/backend/routes"))
    routes_directories.push("/opt/eduk8s/etc/gateway/routes")
    routes_directories.push(...glob.sync("/opt/packages/*/etc/gateway/routes"))
    routes_directories.push("/opt/workshop/gateway/routes")
    routes_directories.push("/home/eduk8s/workshop/gateway/routes")

    console.log("Routes directories:", { paths: routes_directories })

    // Check each route directory for an index file or general router.

    routes_directories.reverse().forEach((directory) => {
        glob.sync(path.join(directory, "*.js")).forEach((filename) => {
            let basename = path.basename(filename, ".js")

            if (basename == "index") {
                console.log("Adding route for index file:", { path: filename })

                app.get("^/?$", require(filename))
            }
            else {
                console.log("Adding route:", { path: filename, prefix: `/${basename}` })

                let router = require(filename)(app, `/${basename}`)

                app.get(`^/${basename}$`, (req, res) => {
                    res.redirect(`/${basename}/`)
                })

                app.use(`/${basename}/`, router)
            }
        })
    })
}
