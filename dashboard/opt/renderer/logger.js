const winston = require("winston");

const level = process.env.LOG_LEVEL || 'debug';

const logger = winston.createLogger({
    transports: [
        new winston.transports.Console({
            level: level,
            timestamp: function () {
                return (new Date()).toISOString();
            }
        })
    ]
});

exports.default = logger;

module.exports = exports.default;
