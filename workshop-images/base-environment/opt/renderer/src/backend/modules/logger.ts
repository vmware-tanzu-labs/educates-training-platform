import { createLogger, format, transports } from "winston"

const { combine, timestamp, prettyPrint } = format

const level = process.env.LOG_LEVEL || "debug"

export const logger = createLogger({
    format: combine(
        timestamp(),
        prettyPrint()
    ),
    transports: [
        new transports.Console({
            level: level
        })
    ]
})
