import * as os from "os"
import * as fs from "fs"
import * as path from "path"

const PLATFORM_ARCH = process.env.PLATFORM_ARCH || ""

const WORKSHOP_NAME = process.env.WORKSHOP_NAME || "workshop"
const TRAINING_PORTAL = process.env.TRAINING_PORTAL || "workshop"
const ENVIRONMENT_NAME = process.env.ENVIRONMENT_NAME || "workshop"
const WORKSHOP_NAMESPACE = process.env.WORKSHOP_NAMESPACE || "workshop"
const SESSION_NAMESPACE = process.env.SESSION_NAMESPACE || "workshop"
const SESSION_NAME = process.env.SESSION_NAME || "workshop"
const SESSION_ID = process.env.SESSION_ID || "workshop"
const SESSION_URL = process.env.SESSION_URL || "http://workshop-127-0-0-1.nip.io"
const SESSION_HOSTNAME = process.env.SESSION_HOSTNAME || "workshop-127-0-0-1.nip.io"

const INGRESS_PROTOCOL = process.env.INGRESS_PROTOCOL || "http"
const INGRESS_DOMAIN = process.env.INGRESS_DOMAIN || "127-0-0-1.nip.io"
const INGRESS_PORT_SUFFIX = process.env.INGRESS_PORT_SUFFIX || ""
const INGRESS_PORT = process.env.INGRESS_PORT || ""
const INGRESS_CLASS = process.env.INGRESS_CLASS || ""

const STORAGE_CLASS = process.env.STORAGE_CLASS || ""

const GOOGLE_TRACKING_ID = process.env.GOOGLE_TRACKING_ID || ""
const CLARITY_TRACKING_ID = process.env.CLARITY_TRACKING_ID || ""
const AMPLITUDE_TRACKING_ID = process.env.AMPLITUDE_TRACKING_ID || ""

const ENABLE_PORTAL = (process.env.PORTAL_URL || "") != ""

const ENABLE_DASHBOARD = process.env.ENABLE_DASHBOARD == "true"

const ENABLE_WORKSHOP = (process.env.ENABLE_WORKSHOP || "true") == "true"
const ENABLE_CONSOLE = process.env.ENABLE_CONSOLE == "true"
const ENABLE_EDITOR = process.env.ENABLE_EDITOR == "true"
const ENABLE_FILES = process.env.ENABLE_FILES == "true"
const ENABLE_EXAMINER = process.env.ENABLE_EXAMINER == "true"
const ENABLE_SLIDES = process.env.ENABLE_SLIDES == "true"
const ENABLE_TERMINAL = process.env.ENABLE_TERMINAL == "true"
const ENABLE_UPLOADS = process.env.ENABLE_UPLOADS == "true"

const ENABLE_COUNTDOWN = process.env.ENABLE_COUNTDOWN == "true"

const CONSOLE_URL = process.env.CONSOLE_URL
const EDITOR_URL = process.env.EDITOR_URL
const SLIDES_URL = process.env.SLIDES_URL

const CONSOLE_PORT = process.env.CONSOLE_PORT
const EDITOR_PORT = process.env.EDITOR_PORT
const WEBDAV_PORT = process.env.WEBDAV_PORT
const WORKSHOP_PORT = process.env.WORKSHOP_PORT

const WORKSHOP_RENDERER = process.env.WORKSHOP_RENDERER
const LOCAL_RENDERER_TYPE = process.env.LOCAL_RENDERER_TYPE

const WORKSHOP_DIR = process.env.WORKSHOP_DIR
const SLIDES_DIR = process.env.SLIDES_DIR
const FILES_DIR = process.env.FILES_DIR
const UPLOADS_DIR = process.env.UPLOADS_DIR

const WORKSHOP_LAYOUT = process.env.WORKSHOP_LAYOUT || "default"
const TERMINAL_LAYOUT = process.env.TERMINAL_LAYOUT || "default"

const RESTART_URL = process.env.RESTART_URL
const FINISHED_MSG = process.env.FINISHED_MSG

const IMAGE_REPOSITORY = process.env.IMAGE_REPOSITORY || "registry.default.svc.cluster.local"
const ASSETS_REPOSITORY = process.env.ASSETS_REPOSITORY || "workshop-assets"

const SERVICES_PASSWORD = process.env.SERVICES_PASSWORD
const CONFIG_PASSWORD = process.env.CONFIG_PASSWORD

function kubernetes_token() {
    if (fs.existsSync("/var/run/secrets/kubernetes.io/serviceaccount/token"))
        return fs.readFileSync("/var/run/secrets/kubernetes.io/serviceaccount/token")
}

function load_workshop() {
    let config_pathname = path.join(os.homedir(), ".local/share/workshop/workshop-definition.json")

    if (!fs.existsSync(config_pathname))
        return {}

    let config_contents = fs.readFileSync(config_pathname, "utf8")

    return JSON.parse(config_contents)
}

export let config = {
    workshop: load_workshop(),

    platform_arch: PLATFORM_ARCH,

    workshop_name: WORKSHOP_NAME,
    training_portal: TRAINING_PORTAL,
    environment_name: ENVIRONMENT_NAME,
    workshop_namespace: WORKSHOP_NAMESPACE,
    session_namespace: SESSION_NAMESPACE,
    session_name: SESSION_NAME,
    session_id: SESSION_ID,
    session_url: SESSION_URL,

    session_hostname: SESSION_HOSTNAME,
    ingress_protocol: INGRESS_PROTOCOL,
    ingress_domain: INGRESS_DOMAIN,
    ingress_port_suffix: INGRESS_PORT_SUFFIX,
    ingress_port: INGRESS_PORT,
    ingress_class: INGRESS_CLASS,

    storage_class: STORAGE_CLASS,

    google_tracking_id: GOOGLE_TRACKING_ID,
    clarity_tracking_id: CLARITY_TRACKING_ID,
    amplitude_tracking_id: AMPLITUDE_TRACKING_ID,

    enable_portal: ENABLE_PORTAL,

    enable_dashboard: ENABLE_DASHBOARD,

    enable_workshop: ENABLE_WORKSHOP,
    enable_console: ENABLE_CONSOLE,
    enable_editor: ENABLE_EDITOR,
    enable_files: ENABLE_FILES,
    enable_examiner: ENABLE_EXAMINER,
    enable_slides: ENABLE_SLIDES,
    enable_terminal: ENABLE_TERMINAL,
    enable_uploads: ENABLE_UPLOADS,

    enable_countdown: ENABLE_COUNTDOWN,

    workshop_dir: WORKSHOP_DIR,
    slides_dir: SLIDES_DIR,
    files_dir: FILES_DIR,
    uploads_dir: UPLOADS_DIR,

    workshop_layout: WORKSHOP_LAYOUT,
    terminal_layout: TERMINAL_LAYOUT,

    console_url: CONSOLE_URL,
    editor_url: EDITOR_URL,
    slides_url: SLIDES_URL,

    console_port: CONSOLE_PORT,
    editor_port: EDITOR_PORT,
    webdav_port: WEBDAV_PORT,
    workshop_port: WORKSHOP_PORT,

    workshop_renderer: WORKSHOP_RENDERER,
    local_renderer_type: LOCAL_RENDERER_TYPE,

    workshop_url: "",
    workshop_proxy: {},
    workshop_path: "",

    restart_url: RESTART_URL,
    finished_msg: FINISHED_MSG,

    kubernetes_token: kubernetes_token(),

    image_repository: IMAGE_REPOSITORY,
    assets_repository: ASSETS_REPOSITORY,

    services_password: SERVICES_PASSWORD,
    config_password: CONFIG_PASSWORD,

    dashboards: [],
    ingresses: [],
}

function substitute_session_params(value: any) {
    if (!value)
        return value

    value = value.split("$(platform_arch)").join(config.platform_arch)
    value = value.split("$(image_repository)").join(config.image_repository)
    value = value.split("$(assets_repository)").join(config.assets_repository)
    value = value.split("$(environment_name)").join(config.environment_name)
    value = value.split("$(workshop_namespace)").join(config.workshop_namespace)
    value = value.split("$(session_namespace)").join(config.session_namespace)
    value = value.split("$(session_name)").join(config.session_name)
    value = value.split("$(session_id)").join(config.session_id)
    value = value.split("$(session_hostname)").join(config.session_hostname)
    value = value.split("$(ingress_domain)").join(config.ingress_domain)
    value = value.split("$(ingress_protocol)").join(config.ingress_protocol)
    value = value.split("$(ingress_port_suffix)").join(config.ingress_port_suffix)
    value = value.split("$(services_password)").join(config.services_password)
    value = value.split("$(config_password)").join(config.config_password)

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

function lookup_application(name) {
    let workshop_spec = config.workshop["spec"]

    if (!workshop_spec)
        return {}

    let workshop_session = config.workshop["spec"]["session"]

    if (!workshop_session)
        return {}

    let applications = workshop_session["applications"]

    if (!applications)
        return {}

    let application = applications[name]

    if (!application)
        return {}

    return application
}

function calculate_workshop_url() {
    let application = lookup_application("workshop")

    return substitute_session_params(application["url"])
}

function calculate_workshop_proxy() {
    let application = lookup_application("workshop")

    if (!application)
        return config.workshop_proxy

    let proxy_details = application["proxy"]

    if (!proxy_details)
        return config.workshop_proxy

    let protocol = substitute_session_params(proxy_details["protocol"]) || "http"
    let host = substitute_session_params(proxy_details["host"])
    let port = proxy_details["port"]
    let headers = proxy_details["headers"] || []
    let rewrite_rules = proxy_details["pathRewrite"] || []

    let change_origin = proxy_details["changeOrigin"]

    if (change_origin === undefined)
        change_origin = true

    if (!port || port == "0")
        port = protocol == "https" ? 443 : 80

    let expanded_headers = []

    for (let item of headers) {
        expanded_headers.push({
            name: item["name"],
            value: substitute_session_params(item["value"] || "")
        })
    }

    return {
        protocol: protocol,
        host: host,
        port: port,
        headers: expanded_headers,
        changeOrigin: change_origin,
        pathRewrite: rewrite_rules,
    }
}

function calculate_workshop_path() {
    let application = lookup_application("workshop")

    let workshop_path = substitute_session_params(application["path"])

    if (!workshop_path)
        return path.join(config.workshop_dir, "public")

    if (path.isAbsolute(workshop_path))
        return workshop_path

    return path.join(config.workshop_path, workshop_path)
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
        all_ingresses.push({ "name": "console", "port": config.console_port, "authentication": { "type": "session" } })

    if (config.enable_editor && config.editor_port)
        all_ingresses.push({ "name": "editor", "port": config.editor_port, "authentication": { "type": "session" } })

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
                        "authentication": ingresses[i]["authentication"] || { "type": "session" },
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

config.workshop_url = calculate_workshop_url()
config.workshop_proxy = calculate_workshop_proxy()
config.workshop_path = calculate_workshop_path()

config.dashboards = calculate_dashboards()
config.ingresses = calculate_ingresses()
