var express = require('express');
var proxy = require('http-proxy-middleware');
var logger = require('../logger');

var enable_terminal = process.env.ENABLE_TERMINAL;

module.exports = function(app, prefix) {
    // Setup proxying to terminal application. If no terminal session is
    // provided, redirect to session 1. This ensures user always get the
    // same session and not a new one each time if refresh the web browser
    // or access same URL from another browser window.

    var router = express.Router();

    if (enable_terminal != 'true') {
        return router;
    }

    router.get('^/?$', function (req, res) {
        res.redirect(req.baseUrl + '/session/1');
    })

    router.use('/static', express.static('/opt/workshop/butterfly/static'));

    router.use(proxy(prefix, {
        target: 'http://127.0.0.1:10081',
        ws: true
    }));

    return router;
}
