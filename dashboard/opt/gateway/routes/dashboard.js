var express = require('express');
var path = require('path');
var fs = require('fs');
var config = require('../config');

var enable_console = process.env.ENABLE_CONSOLE == "true";
var enable_dashboard = process.env.ENABLE_DASHBOARD == "true";
var enable_slides = process.env.ENABLE_SLIDES == "true";
var enable_terminal = process.env.ENABLE_TERMINAL == "true";

var session_namespace = process.env.SESSION_NAMESPACE;

var portal_api_url = process.env.PORTAL_API_URL || '';

var enable_portal = portal_api_url != '';

var enable_countdown = process.env.ENABLE_COUNTDOWN == "true";

module.exports = function(app, prefix) {
    var router = express();

    if (!enable_dashboard) {
        return router;
    }

    router.locals.session_namespace = session_namespace;

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
            workshop_dir = '/home/eduk8s/workshop';
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
        res.render('dashboard');
    });

    return router;
}
