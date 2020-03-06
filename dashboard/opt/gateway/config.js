var fs = require('fs');
var yaml = require('js-yaml');

var config = {
    session_namespace: process.env.SESSION_NAMESPACE || 'workshop',
    ingress_domain: process.env.INGRESS_DOMAIN || 'training.eduk8s.io',
    ingress_protocol: process.env.INGRESS_PROTOCOL || 'http',
};

function load_workshop() {
    var config_pathname = '/opt/eduk8s/config/workshop.yaml';

    if (!fs.existsSync(config_pathname))
        return {}

    var config_contents = fs.readFileSync(config_pathname, 'utf8');

    return yaml.safeLoad(config_contents);
}

function substitute_dashboard_params(value) {
    value = value.split("$(session_namespace)").join(config.session_namespace);
    value = value.split("$(ingress_domain)").join(config.ingress_domain);
    value = value.split("$(ingress_protocol)").join(config.ingress_protocol);

    return value;
}

function string_to_slug(str) {
    str = str.trim();
    str = str.toLowerCase();

    return str
        .replace(/[^a-z0-9 -]/g, "") // remove invalid chars
        .replace(/\s+/g, "-") // collapse whitespace and replace by -
        .replace(/-+/g, "-") // collapse dashes
        .replace(/^-+/, "") // trim - from start of text
        .replace(/-+$/, "") // trim - from end of text
}

function calculate_dashboards() {
    var all_dashboards = [];

    let workshop_spec = config.workshop["spec"];

    if (!workshop_spec) {
        return [];
    }

    let workshop_session = config.workshop["spec"]["session"];

    if (workshop_session) {
        let applications = workshop_session["applications"];

        if (applications) {
            if (applications["editor"] && applications["editor"]["enabled"] === true) {
                all_dashboards.push({"id": "editor","name": "Editor",
                    "url": substitute_dashboard_params(
                        "$(ingress_protocol)://$(session_namespace)-editor.$(ingress_domain)/")});
            }
        }

        let dashboards = workshop_session["dashboards"];

        if (dashboards) {
            for (let i=0; i<dashboards.length; i++) {
                if (dashboards[i]["name"] && dashboards[i]["url"]) {
                    all_dashboards.push({"id": string_to_slug(dashboards[i]["name"]),
                        "name": dashboards[i]["name"],
                        "url": substitute_dashboard_params(dashboards[i]["url"])});
                }
            }
        }
    }

    return all_dashboards;
}

function calculate_ingresses() {
    var all_ingresses = [];

    let workshop_spec = config.workshop["spec"];

    if (!workshop_spec) {
        return [];
    }

    let workshop_session = config.workshop["spec"]["session"];

    if (workshop_session) {
        let applications = workshop_session["applications"];

        if (applications) {
            if (applications["console"] && applications["console"]["enabled"] === true) {
                if (applications["console"]["vendor"] == "octant") {
                    all_ingresses.push({"name": "console", "port": 10086});
                }
                else
                {
                    all_ingresses.push({"name": "console", "port": 10083});
                }
            }
            if (applications["editor"] && applications["editor"]["enabled"] === true) {
                all_ingresses.push({"name": "editor", "port": 10085});
            }
        }

        let ingresses = workshop_session["ingresses"];

        if (ingresses) {
            for (let i=0; i<ingresses.length; i++) {
                if (ingresses[i]["name"] && ingresses[i]["port"]) {
                    all_ingresses.push(ingresses[i]);
                }
            }
        }
    }

    return all_ingresses;
}

config.workshop = load_workshop();
config.dashboards = calculate_dashboards();
config.ingresses = calculate_ingresses();

exports.default = config;

module.exports = exports.default;
