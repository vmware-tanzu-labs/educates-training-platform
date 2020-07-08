var express = require('express');
var path = require('path');
var fs = require('fs');
var config = require('../config');

var enable_console = process.env.ENABLE_CONSOLE == "true";
var enable_dashboard = process.env.ENABLE_DASHBOARD == "true";
var enable_slides = process.env.ENABLE_SLIDES == "true";
var enable_terminal = process.env.ENABLE_TERMINAL == "true";

var google_tracking_id = process.env.GOOGLE_TRACKING_ID || '';

var workshop_name = process.env.WORKSHOP_NAME || '';
var session_namespace = process.env.SESSION_NAMESPACE || '';
var workshop_namespace = process.env.WORKSHOP_NAMESPACE || '';
var training_portal = process.env.TRAINING_PORTAL || '';
var ingress_domain = process.env.INGRESS_DOMAIN || '';
var ingress_protocol = process.env.INGRESS_PROTOCOL || 'http';

var portal_api_url = process.env.PORTAL_API_URL || '';

var enable_portal = portal_api_url != '';

var enable_countdown = process.env.ENABLE_COUNTDOWN == "true";

module.exports = function(app, prefix) {
    var router = express();

    if (!enable_dashboard) {
        return router;
    }

    router.locals.google_tracking_id = google_tracking_id;

    router.locals.workshop_name = workshop_name;
    router.locals.session_namespace = session_namespace;
    router.locals.workshop_namespace = workshop_namespace;
    router.locals.training_portal = training_portal;
    router.locals.ingress_domain = ingress_domain;
    router.locals.ingress_protocol = ingress_protocol;

    router.locals.terminal_layout = process.env.TERMINAL_LAYOUT;

    if (enable_console) {
        router.locals.console_url = process.env.CONSOLE_URL || 'http://localhost:10083';
    }

    router.locals.restart_url = process.env.RESTART_URL;

    router.locals.workshop_link = process.env.WORKSHOP_LINK;
    router.locals.slides_link = process.env.SLIDES_LINK;

    router.locals.homeroom_link = process.env.HOMEROOM_LINK;

    router.locals.finished_msg = process.env.FINISHED_MSG;

    if (!process.env.WORKSHOP_LINK) {
        if (process.env.JUPYTERHUB_ROUTE) {
            router.locals.workshop_link = process.env.JUPYTERHUB_ROUTE;
        }
    }

    router.locals.dashboard_panels = config.dashboards;

    var workshop_dir = process.env.WORKSHOP_DIR;

    var slides_dir = process.env.SLIDES_DIR;

    router.locals.with_slides = false;

    if (slides_dir) {
        if (fs.existsSync(slides_dir + '/index.html')) {
            router.locals.with_slides = true;
        }
        else {
            slides_dir = undefined;
        }
    }

    if (!workshop_dir) {
        if (fs.existsSync('/opt/eduk8s/workshop')) {
            workshop_dir = '/opt/eduk8s/workshop';
        }
        else {
            if (fs.existsSync('/opt/workshop')) {
                workshop_dir = '/opt/Workshop';
            }
            else {
                workshop_dir = '/home/eduk8s/workshop';
            }
        }
    }

    if (!slides_dir) {
        if (fs.existsSync(workshop_dir + '/slides/index.html')) {
            router.locals.with_slides = true;
        }
    }

    if (router.locals.with_slides && !enable_slides) {
        router.locals.with_slides = false;
    }

    router.locals.with_portal = enable_portal;

    router.locals.with_countdown = enable_countdown;

    router.locals.with_console = enable_console;
    router.locals.with_terminal = enable_terminal;

    router.set('views', path.join(__dirname, '..', 'views'));
    router.set('view engine', 'pug');

    router.use(function (req, res) {
        if (!req.session.load_count) {
            req.session.load_count = 1;
        }
        else {
            req.session.load_count = req.session.load_count + 1;
        }

        var locals = { "load_count": req.session.load_count };

        res.render('dashboard', locals);
    });

    return router;
}
