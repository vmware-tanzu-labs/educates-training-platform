import * as express from "express"
import * as path from "path"
import * as fs from "fs"
import * as url from "url"

const BASEDIR = path.dirname(path.dirname(path.dirname(__dirname)))

// Setup handler for default page of site. This is provided by the "index.js"
// file in the "routes" directory. That with this application is used unless
// overridden by a workshop.

function set_default_page(app: express.Application) {
    let default_index = path.join(BASEDIR, "build/backend/routes/index.js")

    let override_index_1 = "/opt/eduk8s/workshop/gateway/routes/index.js"
    let override_index_2 = "/opt/workshop/gateway/routes/index.js"
    let override_index_3 = "/home/eduk8s/workshop/gateway/routes/index.js"

    if (fs.existsSync(override_index_1)) {
        console.log("Set index to", { path: override_index_1 })
        app.get("^/?$", require(override_index_1))
    }
    else if (fs.existsSync(override_index_2)) {
        console.log("Set index to", { path: override_index_2 })
        app.get("^/?$", require(override_index_2))
    }
    else if (fs.existsSync(override_index_3)) {
        console.log("Set index to", { path: override_index_3 })
        app.get("^/?$", require(override_index_3))
    }
    else {
        console.log("Set index to", { path: default_index })
        app.get("^/?$", require(default_index))
    }
}

// Install any routes. These correspond to sub URL where the path is
// dictated by the name of the file in the "routes" directory. The routes
// can come from this application, or be extended by a specific workshop.

function install_routes(app: express.Application, directory: string) {
    if (fs.existsSync(directory)) {
        let files = fs.readdirSync(directory)

        for (let i = 0; i < files.length; i++) {
            let filename = files[i];

            if (filename.endsWith(".js")) {
                let basename = filename.split(".").slice(0, -1).join(".")

                // Skip over the "index.js" file as it is only used for
                // the default page as configured above.

                if (basename == "index")
                    continue

                let prefix = "/" + basename

                app.get("^" + prefix + "$", (req, res) => {
                    res.redirect(url.parse(req.url).pathname + "/")
                })

                let pathname = path.join(directory, filename)
                let router = require(pathname)(app, prefix + "/")

                console.log("Install route for", { path: pathname })

                app.use(prefix + "/", router)
            }
        }
    }
}

// Set the default page for the site and install any routes.

export function setup_routing(app: express.Application) {
    set_default_page(app)

    install_routes(app, path.join(BASEDIR, "build/backend/routes"))

    install_routes(app, "/opt/eduk8s/workshop/gateway/routes")
    install_routes(app, "/opt/workshop/gateway/routes")
    install_routes(app, "/home/eduk8s/workshop/gateway/routes")
}
