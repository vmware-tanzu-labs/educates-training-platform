import * as fs from "fs"
import * as yaml from "js-yaml"

const CONSOLE_KUBERNETES_PORT = 10083
const CONSOLE_OCTANT_PORT = 10086
const CONSOLE_OPENSHIFT_PORT = 10087

const EDITOR_PORT = 10085

const ENVIRONMENT_NAME = process.env.ENVIRONMENT_NAME || "workshop"
const WORKSHOP_NAMESPACE = process.env.WORKSHOP_NAMESPACE || "workshop"
const SESSION_NAMESPACE = process.env.SESSION_NAMESPACE || "workshop"
const INGRESS_DOMAIN = process.env.INGRESS_DOMAIN || "training.eduk8s.io"
const INGRESS_PROTOCOL = process.env.INGRESS_PROTOCOL || "http"

export let config = {
    workshop: {},
    dashboards: [],
    ingresses: [],
    environment_name: ENVIRONMENT_NAME,
    workshop_namespace: WORKSHOP_NAMESPACE,
    session_namespace: SESSION_NAMESPACE,
    ingress_domain: INGRESS_DOMAIN,
    ingress_protocol: INGRESS_PROTOCOL
}

function load_workshop() {
    let config_pathname = "/opt/eduk8s/config/workshop.yaml"

    if (!fs.existsSync(config_pathname))
        return {}

    let config_contents = fs.readFileSync(config_pathname, "utf8")

    return yaml.safeLoad(config_contents)
}

config.workshop = load_workshop()

function substitute_dashboard_params(value: string) {
    value = value.split("$(environment_name)").join(config.environment_name)
    value = value.split("$(workshop_namespace)").join(config.workshop_namespace)
    value = value.split("$(session_namespace)").join(config.session_namespace)
    value = value.split("$(ingress_domain)").join(config.ingress_domain)
    value = value.split("$(ingress_protocol)").join(config.ingress_protocol)

    return value
}

function string_to_slug(str: string) {
    str = str.trim()
    str = str.toLowerCase()

    return str
        .replace(/[^a-z0-9 -]/g, "") // remove invalid chars
        .replace(/\s+/g, "-") // collapse whitespace and replace by -
        .replace(/-+/g, "-") // collapse dashes
        .replace(/^-+/, "") // trim - from start of text
        .replace(/-+$/, "") // trim - from end of text
}

function calculate_dashboards() {
    let all_dashboards = []

    let workshop_spec = config.workshop["spec"]

    if (!workshop_spec) {
        return []
    }

    let workshop_session = config.workshop["spec"]["session"]

    if (workshop_session) {
        let applications = workshop_session["applications"]

        if (applications) {
            if (applications["editor"] && applications["editor"]["enabled"] === true) {
                all_dashboards.push({
                    "id": "editor", "name": "Editor",
                    "url": substitute_dashboard_params(
                        "$(ingress_protocol)://$(session_namespace)-editor.$(ingress_domain)/")
                })
            }
        }

        let dashboards = workshop_session["dashboards"]

        if (dashboards) {
            for (let i = 0; i < dashboards.length; i++) {
                if (dashboards[i]["name"] && dashboards[i]["url"]) {
                    all_dashboards.push({
                        "id": string_to_slug(dashboards[i]["name"]),
                        "name": dashboards[i]["name"],
                        "url": substitute_dashboard_params(dashboards[i]["url"])
                    })
                }
            }
        }
    }

    return all_dashboards
}

function calculate_ingresses() {
    let all_ingresses = []

    let workshop_spec = config.workshop["spec"]

    if (!workshop_spec) {
        return []
    }

    let workshop_session = config.workshop["spec"]["session"]

    if (workshop_session) {
        let applications = workshop_session["applications"]

        if (applications) {
            if (applications["console"] && applications["console"]["enabled"] === true) {
                if (applications["console"]["vendor"] == "openshift") {
                    all_ingresses.push({ "name": "console", "port": CONSOLE_OPENSHIFT_PORT })
                }
                else if (applications["console"]["vendor"] == "octant") {
                    all_ingresses.push({ "name": "console", "port": CONSOLE_OCTANT_PORT })
                }
                else {
                    all_ingresses.push({ "name": "console", "port": CONSOLE_KUBERNETES_PORT })
                }
            }
            if (applications["editor"] && applications["editor"]["enabled"] === true) {
                all_ingresses.push({ "name": "editor", "port": EDITOR_PORT })
            }
        }

        let ingresses = workshop_session["ingresses"]

        if (ingresses) {
            for (let i = 0; i < ingresses.length; i++) {
                if (ingresses[i]["name"] && ingresses[i]["port"]) {
                    all_ingresses.push(ingresses[i])
                }
            }
        }
    }

    return all_ingresses
}

config.dashboards = calculate_dashboards()
config.ingresses = calculate_ingresses()