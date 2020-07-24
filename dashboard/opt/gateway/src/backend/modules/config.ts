import * as fs from "fs"
import * as yaml from "js-yaml"

const CONSOLE_KUBERNETES_PORT = 10083
const CONSOLE_OCTANT_PORT = 10086
const CONSOLE_OPENSHIFT_PORT = 10087

const EDITOR_PORT = 10085

const WORKSHOP_NAME = process.env.WORKSHOP_NAME || "workshop"
const TRAINING_PORTAL = process.env.TRAINING_PORTAL || "workshop"
const ENVIRONMENT_NAME = process.env.ENVIRONMENT_NAME || "workshop"
const WORKSHOP_NAMESPACE = process.env.WORKSHOP_NAMESPACE || "workshop"
const SESSION_NAMESPACE = process.env.SESSION_NAMESPACE || "workshop"

const INGRESS_PROTOCOL = process.env.INGRESS_PROTOCOL || "http"
const INGRESS_DOMAIN = process.env.INGRESS_DOMAIN || "training.eduk8s.io"

const GOOGLE_TRACKING_ID = process.env.GOOGLE_TRACKING_ID || ""

const ENABLE_PORTAL = (process.env.PORTAL_API_URL || "") != ""

const ENABLE_DASHBOARD = process.env.ENABLE_DASHBOARD == "true"

const ENABLE_WORKSHOP = (process.env.ENABLE_WORKSHOP || "true") == "true"
const ENABLE_CONSOLE = process.env.ENABLE_CONSOLE == "true"
const ENABLE_EDITOR = process.env.ENABLE_EDITOR == "true"
const ENABLE_SLIDES = process.env.ENABLE_SLIDES == "true"
const ENABLE_TERMINAL = process.env.ENABLE_TERMINAL == "true"

const ENABLE_COUNTDOWN = process.env.ENABLE_COUNTDOWN == "true"

const TERMINAL_LAYOUT = process.env.TERMINAL_LAYOUT || "default"

const RESTART_URL = process.env.RESTART_URL
const FINISHED_MSG = process.env.FINISHED_MSG

function load_workshop() {
    let config_pathname = "/opt/eduk8s/config/workshop.yaml"

    if (!fs.existsSync(config_pathname))
        return {}

    let config_contents = fs.readFileSync(config_pathname, "utf8")

    return yaml.safeLoad(config_contents)
}

export let config = {
    workshop: load_workshop(),

    workshop_name: WORKSHOP_NAME,
    training_portal: TRAINING_PORTAL,
    environment_name: ENVIRONMENT_NAME,
    workshop_namespace: WORKSHOP_NAMESPACE,
    session_namespace: SESSION_NAMESPACE,

    ingress_protocol: INGRESS_PROTOCOL,
    ingress_domain: INGRESS_DOMAIN,

    google_tracking_id: GOOGLE_TRACKING_ID,

    enable_portal: ENABLE_PORTAL,

    enable_dashboard: ENABLE_DASHBOARD,

    enable_workshop: ENABLE_WORKSHOP,
    enable_console: ENABLE_CONSOLE,
    enable_editor: ENABLE_EDITOR,
    enable_slides: ENABLE_SLIDES,
    enable_terminal: ENABLE_TERMINAL,

    enable_countdown: ENABLE_COUNTDOWN,

    terminal_layout: TERMINAL_LAYOUT,

    restart_url: RESTART_URL,
    finished_msg: FINISHED_MSG,

    dashboards: [],
    ingresses: [],
}

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