import * as fs from "fs"
import * as path from "path"
import * as yaml from "js-yaml"

const BASEDIR = path.dirname(path.dirname(path.dirname(__dirname)))

export let config = {
    // Log format for messages and request logging.

    log_format: process.env.LOG_FORMAT || "dev",

    // Port that the application server listens on.

    server_port: parseInt(process.env.WORKSHOP_PORT || "10082"),

    // Specifies the path of workshop folder where the workshop files are
    // located. This will be overridden down below to look in other valid
    // places that content can be kept.

    workshop_dir: path.join(BASEDIR, "workshop"),

    // Specifies the path of config file for workshop. This will be overridden
    // down below to look in other valid places that content can be kept.

    config_file: path.join(BASEDIR, "workshop/config.js"),

    // Specifies the path of content folder where all content files are
    // located. This will be overridden down below to look in other valid
    // places that content can be kept.

    content_dir: path.join(BASEDIR, "workshop/content"),

    // URL where the users should be redirected to restart the workshop when
    // they reach the final page.

    restart_url: process.env.RESTART_URL,

    // Default workshop site title. Appears in page banner.

    site_title: "Educates",

    // Training portal, workshop and session configuration.

    platform_arch: process.env.PLATFORM_ARCH || "",
    image_repository: process.env.IMAGE_REPOSITORY || "registry.default.svc.cluster.local",
    oci_image_cache: process.env.OCI_IMAGE_CACHE || "workshop-images",
    assets_repository: process.env.ASSETS_REPOSITORY || "workshop-assets",
    workshop_name: process.env.WORKSHOP_NAME || "workshop",
    environment_name: process.env.ENVIRONMENT_NAME || "workshop",
    session_name: process.env.SESSION_NAME || "workshop",
    session_id: process.env.SESSION_ID || "workshop",
    session_url: process.env.SESSION_URL || "http://workshop-127-0-0-1.nip.io",
    session_namespace: process.env.SESSION_NAMESPACE || "workshop",
    workshop_namespace: process.env.WORKSHOP_NAMESPACE || "workshop",
    training_portal: process.env.TRAINING_PORTAL || "workshop",
    session_hostname: process.env.SESSION_HOSTNAME || "workshop-127-0-0-1.nip.io",
    cluster_domain: process.env.CLUSTER_DOMAIN || "cluster.local",
    ingress_domain: process.env.INGRESS_DOMAIN || "127-0-0-1.nip.io",
    ingress_protocol: process.env.INGRESS_PROTOCOL || "http",
    ingress_port_suffix: process.env.INGRESS_PORT_SUFFIX || "",
    ingress_port: process.env.INGRESS_PORT || "",
    ingress_class: process.env.INGRESS_CLASS || "",
    storage_class: process.env.STORAGE_CLASS || "",
    policy_engine: process.env.POLICY_ENGINE || "none",
    policy_name: process.env.POLICY_NAME || "restricted",
    services_password: process.env.SERVICES_PASSWORD || "",
    config_password: process.env.CONFIG_PASSWORD || "",

    // Google and Clarity analytics tracking ID.

    google_tracking_id: process.env.GOOGLE_TRACKING_ID || "",
    clarity_tracking_id: process.env.CLARITY_TRACKING_ID || "",
    amplitude_tracking_id: process.env.AMPLITUDE_TRACKING_ID || "",

    // List of workshop modules. Can define "path" to page, without extension.
    // The page can either be Markdown (.md) or AsciiDoc (.adoc). Name of page
    // should be give by "title". Any document title in an AsciiDoc page will
    // be ignored. If no title is given it will be generated from name of
    // file. Label on the button to go to next page can be overridden by
    // "exit_sign".

    modules: [
        /*
        {
            "path": "index",
            "title": "Workshop Overview",
            "exit_sign": "Setup Workshop",
        },
        {
            "path": "setup",
            "title": "Workshop Setup",
            "exit_sign": "Start Workshop",
        },
        {
            "path": "exercies/step-1",
            "title": "User Steps 1",
        },
        {
            "path": "exercies/step-2",
            "title": "User Steps 2",
            "exit_sign": "Finish Workshop",
        },
        {
            "path": "finish",
            "title": "Workshop Finished",
            "exit_sign": "Restart Workshop",
        },
        */
    ],

    // List of variables available for interpolation in content. Where a user
    // supplied config.js provides variables, entries from it will be appended
    // to these. We also add more default variables down below.

    variables: [],
}

config.variables.push({ name: "platform_arch", content: config.platform_arch })
config.variables.push({ name: "image_repository", content: config.image_repository })
config.variables.push({ name: "oci_image_cache", content: config.oci_image_cache })
config.variables.push({ name: "assets_repository", content: config.assets_repository })
config.variables.push({ name: "workshop_name", content: config.workshop_name })
config.variables.push({ name: "environment_name", content: config.environment_name })
config.variables.push({ name: "session_name", content: config.session_name })
config.variables.push({ name: "session_id", content: config.session_id })
config.variables.push({ name: "session_url", content: config.session_url })
config.variables.push({ name: "session_namespace", content: config.session_namespace })
config.variables.push({ name: "workshop_namespace", content: config.workshop_namespace })
config.variables.push({ name: "training_portal", content: config.training_portal })
config.variables.push({ name: "session_hostname", content: config.session_hostname })
config.variables.push({ name: "cluster_domain", content: config.cluster_domain })
config.variables.push({ name: "ingress_domain", content: config.ingress_domain })
config.variables.push({ name: "ingress_protocol", content: config.ingress_protocol })
config.variables.push({ name: "ingress_port_suffix", content: config.ingress_port_suffix })
config.variables.push({ name: "ingress_port", content: config.ingress_port })
config.variables.push({ name: "ingress_class", content: config.ingress_class })
config.variables.push({ name: "storage_class", content: config.storage_class })
config.variables.push({ name: "policy_engine", content: config.policy_engine })
config.variables.push({ name: "policy_name", content: config.policy_name })
config.variables.push({ name: "services_password", content: config.services_password })
config.variables.push({ name: "config_password", content: config.config_password })

if (fs.existsSync("/var/run/secrets/kubernetes.io/serviceaccount/token")) {
    let data = fs.readFileSync("/var/run/secrets/kubernetes.io/serviceaccount/token")
    config.variables.push({ name: "kubernetes_token", content: data })
}

if (fs.existsSync("/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")) {
    let data = fs.readFileSync("/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")
    config.variables.push({ name: "kubernetes_ca_crt", content: data })
}

if (fs.existsSync("/home/eduk8s/.ssh/id_rsa")) {
    let data = fs.readFileSync("/home/eduk8s/.ssh/id_rsa")
    config.variables.push({ name: "ssh_private_key", content: data })
}

if (fs.existsSync("/home/eduk8s/.ssh/id_rsa.pub")) {
    let data = fs.readFileSync("/home/eduk8s/.ssh/id_rsa.pub")
    config.variables.push({ name: "ssh_public_key", content: data })
}

config.variables.push({ name: "kubernetes_api_url", content: process.env.KUBERNETES_API_URL || "" })

if (process.env.ENABLE_REGISTRY == "true") {
    config.variables.push({ name: "registry_host", content: process.env.REGISTRY_HOST || "" })
    config.variables.push({ name: "registry_auth_file", content: process.env.REGISTRY_AUTH_FILE || "" })
    config.variables.push({ name: "registry_username", content: process.env.REGISTRY_USERNAME || "" })
    config.variables.push({ name: "registry_password", content: process.env.REGISTRY_PASSWORD || "" })
    config.variables.push({ name: "registry_auth_token", content: process.env.REGISTRY_AUTH_TOKEN || "" })
    config.variables.push({ name: "registry_secret", content: process.env.REGISTRY_SECRET || "" })
}

if (process.env.ENABLE_GIT == "true") {
    config.variables.push({ name: "git_protocol", content: process.env.INGRESS_PROTOCOL || "" })
    config.variables.push({ name: "git_host", content: process.env.GIT_HOST || "" })
    config.variables.push({ name: "git_username", content: process.env.GIT_USERNAME || "" })
    config.variables.push({ name: "git_password", content: process.env.GIT_PASSWORD || "" })
    config.variables.push({ name: "git_auth_token", content: process.env.GIT_AUTH_TOKEN || "" })
}

for (let key in process.env)
    config.variables.push({ name: "ENV_" + key, content: process.env[key] })

// Check various locations for content and config.

let workshop_file = process.env.WORKSHOP_FILE || "workshop.yaml"

let workshop_dir = process.env.WORKSHOP_DIR || "/opt/workshop"

if (workshop_dir && fs.existsSync(path.join(workshop_dir, "content"))) {
    config.workshop_dir = workshop_dir
    config.config_file = path.join(config.workshop_dir, "config.js")
    config.content_dir = path.join(config.workshop_dir, "content")
}
else {
    workshop_dir = "/opt/eduk8s/workshop"

    if (fs.existsSync(path.join(workshop_dir, "content"))) {
        config.workshop_dir = workshop_dir
        config.config_file = path.join(config.workshop_dir, "config.js")
        config.content_dir = path.join(config.workshop_dir, "content")
    }
    else {
        workshop_dir = "/opt/workshop"

        if (fs.existsSync(path.join(workshop_dir, "content"))) {
            config.workshop_dir = workshop_dir
            config.config_file = path.join(config.workshop_dir, "config.js")
            config.content_dir = path.join(config.workshop_dir, "content")
        }
        else {
            workshop_dir = "/home/eduk8s/workshop"

            if (fs.existsSync(path.join(workshop_dir, "content"))) {
                config.workshop_dir = workshop_dir
                config.config_file = path.join(config.workshop_dir, "config.js")
                config.content_dir = path.join(config.workshop_dir, "content")
            }
        }
    }
}

// If user config.js is supplied with alternate content, merge it with the
// configuration above.

function process_workshop_config(workshop_config = undefined) {
    if (workshop_config === undefined)
        workshop_config = require(config.config_file)

    if (typeof workshop_config != "function")
        return workshop_config

    let temp_config = {
        site_title: "Educates",

        google_tracking_id: "",
        clarity_tracking_id: "",
        amplitude_tracking_id: "",

        modules: [],

        variables: [],
    }

    function site_title(title) {
        temp_config.site_title = title
    }

    function google_tracking_id(id) {
        if (id)
            temp_config.google_tracking_id = id
    }

    function clarity_tracking_id(id) {
        if (id)
            temp_config.clarity_tracking_id = id
    }

    function amplitude_tracking_id(id) {
        if (id)
            temp_config.amplitude_tracking_id = id
    }

    function module_metadata(pathname, title, exit_sign) {
        temp_config.modules.push({ path: pathname, title: title, exit_sign: exit_sign })
    }

    function data_variable(name, value, aliases = undefined) {
        if (typeof aliases == "string")
            aliases = [aliases]

        if (aliases !== undefined) {
            for (let i = 0; i < aliases.length; i++) {
                let alias = aliases[i]
                if (process.env[alias] !== undefined) {
                    value = process.env[alias]
                    break
                }
            }
        }
        else {
            if (process.env[name] !== undefined)
                value = process.env[name]
        }

        temp_config.variables.push({ name: name, content: value })
    }

    function load_workshop(pathname) {
        if (pathname === undefined)
            pathname = workshop_file

        // Read the workshops file first to get the site title and list of
        // activated workshops.

        pathname = path.join(config.workshop_dir, pathname)

        let workshop_data = fs.readFileSync(pathname, "utf8")
        let workshop_info: any = yaml.load(workshop_data)

        temp_config.site_title = workshop_info.name

        // Now iterate over list of activated modules and populate modules
        // list in config.

        pathname = path.join(config.workshop_dir, "modules.yaml")

        let modules_data = fs.readFileSync(pathname, "utf8")
        let modules_info: any = yaml.load(modules_data)

        for (let i = 0; i < workshop_info.modules.activate.length; i++) {
            let name = workshop_info.modules.activate[i]
            let module_info = modules_info.modules[name]

            if (module_info)
                module_metadata(name, module_info.name, module_info.exit_sign)
        }

        // Next set data variables and any other config settings from the
        // modules file.

        let modules_conf = modules_info.config || {}

        google_tracking_id(modules_conf.google_tracking_id)
        clarity_tracking_id(modules_conf.clarity_tracking_id)
        amplitude_tracking_id(modules_conf.amplitude_tracking_id)

        let variables_set = new Set()

        if (modules_conf.vars) {
            for (let i = 0; i < modules_conf.vars.length; i++) {
                let vars_info = modules_conf.vars[i]

                let name = vars_info.name
                let value = vars_info.value
                let aliases = vars_info.aliases

                // We override default value with that from the workshop file
                // if specified.

                if (workshop_info.vars) {
                    if (workshop_info.vars[name] !== undefined)
                        value = workshop_info.vars[name]
                }

                variables_set.add(name)

                data_variable(name, value, aliases)
            }
        }

        // Now override any data variables from the workshop file if haven't
        // already added them.

        if (workshop_info.vars) {
            for (let name in workshop_info.vars) {
                if (!variables_set.has(name))
                    data_variable(name, workshop_info.vars[name])
            }
        }

        // Add special data variable to allow copying of inline text when
        // clicked.

        data_variable("copy", "<sup class='inline-copy far fa-copy' aria-hidden='true'></sup>")
    }

    let workshop = {
        config: temp_config,
        site_title: site_title,
        google_tracking_id: google_tracking_id,
        clarity_tracking_id: clarity_tracking_id,
        amplitude_tracking_id: amplitude_tracking_id,
        module_metadata: module_metadata,
        data_variable: data_variable,
        load_workshop: load_workshop,
    }

    workshop_config(workshop)

    return temp_config
}

const allowed_config = new Set([
    "site_title",
    "modules",
    "variables",
])

export function initialize_workshop() {
    let override_config

    if (fs.existsSync(config.config_file)) {
        // User provided config.js file.

        override_config = process_workshop_config()
    }
    else {
        // User provided workshop.yaml file.

        let file = path.join(config.workshop_dir, workshop_file)

        if (fs.existsSync(file)) {
            override_config = process_workshop_config((workshop) => {
                workshop.load_workshop(workshop_file)
            })
        }
    }

    if (override_config) {
        for (var key1 in override_config) {
            if (allowed_config.has(key1)) {
                let value1 = override_config[key1]
                if (value1 !== undefined && value1 != null) {
                    if (value1.constructor == Array) {
                        config[key1] = config[key1].concat(value1)
                    }
                    else if (value1.constructor == Object) {
                        for (let key2 in value1) {
                            config[key1][key2] = value1[key2]
                        }
                    }
                    else {
                        config[key1] = value1
                    }
                }
            }
        }
    }
}
