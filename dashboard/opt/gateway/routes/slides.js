var express = require('express');
var fs = require('fs');

var enable_slides = process.env.ENABLE_SLIDES;

var workshop_dir = process.env.WORKSHOP_DIR || '/home/eduk8s/workshop';

var slides_dir = process.env.SLIDES_DIR;

module.exports = function(app, prefix) {
    var router = express.Router();

    if (enable_slides != 'true') {
        return router;
    }

    if (slides_dir) {
        if (!fs.existsSync(slides_dir + '/index.html')) {
            slides_dir = undefined;
        }
    }

    if (!slides_dir) {
        if (fs.existsSync(workshop_dir + '/slides/index.html')) {
            slides_dir = workshop_dir + '/slides';
        }
    }

    if (slides_dir) {
        router.use(express.static(slides_dir));
        router.use(express.static('/opt/revealjs'));
    }

    return router;
}
