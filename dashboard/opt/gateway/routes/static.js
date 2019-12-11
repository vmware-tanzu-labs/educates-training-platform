var express = require('express');
var path = require('path');

module.exports = function(app, prefix) {
    var router = express.Router();

    router.use(express.static(path.join(__dirname, '..', 'static')));

    return router;
}
