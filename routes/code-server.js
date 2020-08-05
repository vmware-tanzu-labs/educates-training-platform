var express = require('express');
var { createProxyMiddleware } = require('http-proxy-middleware');

var enable_editor = process.env.ENABLE_EDITOR;

module.exports = function(app, prefix) {
    var router = express.Router();

    if (enable_editor != 'true') {
        return router;
    }

    router.use(createProxyMiddleware(prefix, {
        target: 'http://127.0.0.1:10011',
        pathRewrite: {
            ['^' + prefix]: ''
        },
    }));

    return router;
}
