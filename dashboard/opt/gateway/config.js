var fs = require('fs');
var yaml = require('js-yaml');

var session_namespace = process.env.SESSION_NAMESPACE;
var ingress_domain = process.env.INGRESS_DOMAIN || 'training.eduk8s.io';
var ingress_protocol = process.env.INGRESS_PROTOCOL || 'http';

function load_gateway_config() {
    var config_pathname = '/home/eduk8s/workshop/gateway.yaml';

    if (!fs.existsSync(config_pathname))
        return {}

    var config_contents = fs.readFileSync(config_pathname, 'utf8');

    var data = yaml.safeLoad(config_contents);

    var proxies = data["proxies"] || [];

    var processed_proxies = [];

    for (let i=0; i<proxies.length; i++) {
        let proxy = proxies[i];
        if (proxy["name"] && proxy["port"]) {
            processed_proxies.push(proxy);
        }
    }

    data["proxies"] = processed_proxies;

    var panels = data["panels"] || [];

    var processed_panels = [];

    for (let i=0; i<panels.length; i++) {
        let panel = panels[i];
        if (panel["name"] && panel["url"]) {
            let url = panel["url"];
            url = url.split("$(session_namespace)").join(session_namespace);
            url = url.split("$(ingress_domain)").join(ingress_domain);
            url = url.split("$(ingress_protocol)").join(ingress_protocol);
            processed_panels.push({"name":panel["name"], "url":url,
                "id": i.toString()});
        }
    }

    data["panels"] = processed_panels;

    return data;
}

var config = {
    gateway_config: load_gateway_config()
};

exports.default = config;

module.exports = exports.default;
