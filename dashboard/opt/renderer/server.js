var express = require('express');
var morgan = require('morgan')
var path = require('path')

// Read in global configuation.

var config = require('./config.js');

// Setup the root for the application.

var app = express();

app.enable('strict routing');

// Add logging for inbound request.

var logger = require('./logger.js');

app.use(morgan(config.log_format));

// Setup template rendering engine.

const { Liquid } = require('liquidjs');

const engine = new Liquid({
  root: path.join(__dirname, 'views'),
  extname: '.liquid'
});

app.engine('liquid', engine.express())
app.set('view engine', 'liquid')

// Setup handlers for routes.

var routes = require('./routes.js');

app.use(config.base_url, routes);

// In OpenShift we are always behind a proxy, so trust the headers sent.

app.set('trust proxy', true);

// Start the application listener.

logger.info('Starting listener', { port: config.server_port });

app.listen(config.server_port);
