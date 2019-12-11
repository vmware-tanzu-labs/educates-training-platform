var express = require('express');
var proxy = require('http-proxy-middleware');
var axios = require('axios');
var axios_retry = require('axios-retry');
var fs = require('fs');

module.exports = function(app, prefix) {
    var router = express.Router();

    router.get('/.redirect-when-workshop-is-ready', function (req, res) {
        var client = axios.create({ baseURL: 'http://127.0.0.1:10082' });

        var options = {
            retries: 3,
            retryDelay: (retryCount) => {
                return retryCount * 500;
            }
        };

        axios_retry(client, options);

        client.get(req.baseUrl + '/')
            .then(result => {
                res.redirect(req.baseUrl + '/');
            });
    })

    router.use(proxy(prefix, {
        target: 'http://127.0.0.1:10082',
    }));

    return router;
}
