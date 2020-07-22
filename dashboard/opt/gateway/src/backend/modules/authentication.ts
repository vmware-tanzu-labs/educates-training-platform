import * as express from "express"
import * as basic_auth from "express-basic-auth"

// For standalone container deployment of workshop, provide the ability to
// enable authentication using HTTP Basic authentication. In this case there
// will be no user object added to the client session.

const AUTH_USERNAME = process.env.AUTH_USERNAME
const AUTH_PASSWORD = process.env.AUTH_PASSWORD

async function install_basic_auth(app: express.Application) {
    console.log("Register basic auth handler")

    app.use(basic_auth({
        challenge: true,
        realm: "Terminal",
        authorizer: (username: string, password: string) => {
            return username == AUTH_USERNAME && password == AUTH_PASSWORD
        }
    }))
}

// For OAuth access a handshake is perform against the portal web application.
// This mode of operation is setup by the following environment variables.

const PORTAL_CLIENT_ID = process.env.PORTAL_CLIENT_ID
const PORTAL_CLIENT_SECRET = process.env.PORTAL_CLIENT_SECRET
const PORTAL_API_URL = process.env.PORTAL_API_URL

const DASHBOARD_URL = process.env.DASHBOARD_URL

const SESSION_NAME = process.env.SESSION_NAME

async function install_portal_auth(app: express.Application) {
}

// Authentication via OAuth always has priority if configuration for HTTP
// basic authentication is also provided. Setting HTTP basic authentication
// password to "*" has side affect of disabling authentication. This is to
// cope with situation where wasn't possible to prevent the passing of any
// environment variables because of them being required parameters in a
// template.

export async function setup_authentication(app: express.Application) {
    if (PORTAL_CLIENT_ID) {
        console.log("Install portal oauth support.")

        await install_portal_auth(app)
    }
    else if (AUTH_USERNAME) {
        if (AUTH_USERNAME != "*") {
            console.log("Install HTTP Basic auth support.")

            await install_basic_auth(app)
        }
        else {
            console.log("All authentication has been disabled.")
        }
    }
}