import * as fs from "fs"
import * as yaml from "js-yaml"

const WORKSHOP_NAME = process.env.WORKSHOP_NAME || "workshop"
const TRAINING_PORTAL = process.env.TRAINING_PORTAL || "workshop"
const ENVIRONMENT_NAME = process.env.ENVIRONMENT_NAME || "workshop"
const WORKSHOP_NAMESPACE = process.env.WORKSHOP_NAMESPACE || "workshop"
const SESSION_NAMESPACE = process.env.SESSION_NAMESPACE || "workshop"

const INGRESS_PROTOCOL = process.env.INGRESS_PROTOCOL || "http"
const INGRESS_DOMAIN = process.env.INGRESS_DOMAIN || "127.0.0.1.nip.io"
const INGRESS_PORT_SUFFIX = process.env.INGRESS_PORT_SUFFIX || ""

const GOOGLE_TRACKING_ID = process.env.GOOGLE_TRACKING_ID || ""

const ENABLE_PORTAL = (process.env.PORTAL_API_URL || "") != ""

const ENABLE_DASHBOARD = process.env.ENABLE_DASHBOARD == "true"

const ENABLE_WORKSHOP = (process.env.ENABLE_WORKSHOP || "true") == "true"
const ENABLE_CONSOLE = process.env.ENABLE_CONSOLE == "true"
const ENABLE_EDITOR = process.env.ENABLE_EDITOR == "true"
const ENABLE_FILES = process.env.ENABLE_FILES == "true"
const ENABLE_EXAMINER = process.env.ENABLE_EXAMINER == "true"
const ENABLE_SLIDES = process.env.ENABLE_SLIDES == "true"
const ENABLE_TERMINAL = process.env.ENABLE_TERMINAL == "true"

const ENABLE_COUNTDOWN = process.env.ENABLE_COUNTDOWN == "true"

const CONSOLE_URL = process.env.CONSOLE_URL
const EDITOR_URL = process.env.EDITOR_URL
const SLIDES_URL = process.env.SLIDES_URL

const CONSOLE_PORT = process.env.CONSOLE_PORT
const EDITOR_PORT = process.env.EDITOR_PORT
const HTTPD_PORT = process.env.HTTPD_PORT
const WORKSHOP_PORT = process.env.WORKSHOP_PORT

const WORKSHOP_URL = process.env.WORKSHOP_URL

const WORKSHOP_DIR = process.env.WORKSHOP_DIR
const SLIDES_DIR = process.env.SLIDES_DIR

const TERMINAL_LAYOUT = process.env.TERMINAL_LAYOUT || "default"

const RESTART_URL = process.env.RESTART_URL
const FINISHED_MSG = process.env.FINISHED_MSG

function kubernetes_token() {
    if (fs.existsSync("/var/run/secrets/kubernetes.io/serviceaccount/token"))
        return fs.readFileSync("/var/run/secrets/kubernetes.io/serviceaccount/token")
}

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
    ingress_port_suffix: INGRESS_PORT_SUFFIX,

    google_tracking_id: GOOGLE_TRACKING_ID,

    enable_portal: ENABLE_PORTAL,

    enable_dashboard: ENABLE_DASHBOARD,

    enable_workshop: ENABLE_WORKSHOP,
    enable_console: ENABLE_CONSOLE,
    enable_editor: ENABLE_EDITOR,
    enable_files: ENABLE_FILES,
    enable_examiner: ENABLE_EXAMINER,
    enable_slides: ENABLE_SLIDES,
    enable_terminal: ENABLE_TERMINAL,

    enable_countdown: ENABLE_COUNTDOWN,

    workshop_dir: WORKSHOP_DIR,
    slides_dir: SLIDES_DIR,

    terminal_layout: TERMINAL_LAYOUT,

    console_url: CONSOLE_URL,
    editor_url: EDITOR_URL,
    slides_url: SLIDES_URL,

    console_port: CONSOLE_PORT,
    editor_port: EDITOR_PORT,
    httpd_port: HTTPD_PORT,
    workshop_port: WORKSHOP_PORT,

    workshop_url: WORKSHOP_URL,

    restart_url: RESTART_URL,
    finished_msg: FINISHED_MSG,

    kubernetes_token: kubernetes_token(),

    dashboards: [],
    ingresses: [],
}

function substitute_session_params(value: string) {
    value = value.split("$(environment_name)").join(config.environment_name)
    value = value.split("$(workshop_namespace)").join(config.workshop_namespace)
    value = value.split("$(session_namespace)").join(config.session_namespace)
    value = value.split("$(ingress_domain)").join(config.ingress_domain)
    value = value.split("$(ingress_protocol)").join(config.ingress_protocol)
    value = value.split("$(ingress_port_suffix)").join(config.ingress_port_suffix)

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

    if (config.enable_console && config.console_url) {
        all_dashboards.push({
            "id": "console",
            "name": "Console",
            "url": config.console_url
        })
    }

    if (config.enable_editor && config.editor_url) {
        all_dashboards.push({
            "id": "editor",
            "name": "Editor",
            "url": config.editor_url
        })
    }

    if (config.enable_slides && config.slides_url) {
        all_dashboards.push({
            "id": "slides",
            "name": "Slides",
            "url": config.slides_url
        })
    }

    let workshop_spec = config.workshop["spec"]

    if (!workshop_spec)
        return all_dashboards

    let workshop_session = config.workshop["spec"]["session"]

    if (workshop_session) {
        let dashboards = workshop_session["dashboards"]

        if (dashboards) {
            for (let i = 0; i < dashboards.length; i++) {
                if (dashboards[i]["name"]) {
                    let url: string = dashboards[i]["url"]
                    let terminal: string = null

                    url = substitute_session_params(url)

                    if (url.startsWith("terminal:")) {
                        terminal = url.replace("terminal:", "")
                        url = null
                    }

                    all_dashboards.push({
                        "id": string_to_slug(dashboards[i]["name"]),
                        "name": dashboards[i]["name"],
                        "terminal": terminal,
                        "url": url
                    })
                }
            }
        }
    }

    return all_dashboards
}

function calculate_ingresses() {
    let all_ingresses = []

    if (config.enable_console && config.console_port)
        all_ingresses.push({ "name": "console", "port": config.console_port })

    if (config.enable_editor && config.editor_port)
        all_ingresses.push({ "name": "editor", "port": config.editor_port })

    let workshop_spec = config.workshop["spec"]

    if (!workshop_spec)
        return all_ingresses

    let workshop_session = config.workshop["spec"]["session"]

    if (workshop_session) {
        let ingresses = workshop_session["ingresses"]

        if (ingresses) {
            for (let i = 0; i < ingresses.length; i++) {
                if (ingresses[i]["name"]) {
                    all_ingresses.push({
                        "name": ingresses[i]["name"],
                        "host": substitute_session_params(ingresses[i]["host"] || ""),
                        "port": ingresses[i]["port"],
                        "protocol": ingresses[i]["protocol"],
                        "headers": ingresses[i]["headers"] || []
                    })
                }
            }
        }
    }

    return all_ingresses
}

config.dashboards = calculate_dashboards()
config.ingresses = calculate_ingresses()

config.workshop_url = substitute_session_params(config.workshop_url)
