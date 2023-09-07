import * as express from "express"
import * as child_process from "child_process"
import * as path from "path"
import * as fs from "fs"

import { config } from "./config"

const test_program_directories = [
    "/home/eduk8s/workshop/examiner/tests",
    "/opt/workshop/examiner/tests",
    "/opt/eduk8s/workshop/examiner/tests",
    "/opt/renderer/workshop/examiner/tests"
];

function find_test_program(name) {
    let i: any;

    for (i in test_program_directories) {
        let pathname = path.join(test_program_directories[i], name);

        try {
            fs.accessSync(pathname, fs.constants.R_OK | fs.constants.X_OK);
            return pathname;
        } catch (err) {
            // Ignore it.
        }
    }
}

export function setup_examiner(app: express.Application, token: string = null) {
    if (!config.enable_examiner)
        return

    app.use("/examiner/test/", express.json());

    async function examiner_test(req, res, next) {
        let test = req.params.test

        let options = req.body

        let timeout = options.timeout || 15
        let args = options.args || []
        let form = options.form || {}

        if (!test)
            return next()

        let pathname = find_test_program(test)

        if (!pathname)
            return res.sendStatus(404)

        let process: any

        try {
            let timer: any

            process = child_process.spawn(pathname, args)

            process.on('error', (err) => {
                console.error(`${test}: Test failed to execute - ${err}`)

                let result = {
                    success: false,
                    message: "Test failed to execute"
                }

                return res.json(result)
            })

            process.on('exit', (code) => {
                console.log(`${test}: Exited with status ${code}`)

                if (timer)
                    clearTimeout(timer)

                let result = {
                    success: true,
                    message: "Test successfully completed"
                }

                if (code !== 0) {
                    result["success"] = false

                    if (code === null)
                        result["message"] = "Process killed or crashed"
                    else
                        result["message"] = "Test failed to complete"
                }

                return res.json(result)
            })

            process.on('spawn', () => {
                console.log(`${test}: Spawned successfully`)

                if (form) {
                    process.stdin.setEncoding('utf-8')
                    process.stdin.write(JSON.stringify(form))
                }

                process.stdin.end()
            })

            process.stdout.on('data', (data) => {
                console.log(`${test}: ${data}`)
            })

            process.stderr.on('data', (data) => {
                console.error(`${test}: ${data}`)
            })

            if (timeout) {
                console.log(`${test}: timeout=${options.timeout}`)
                timer = setTimeout(() => {
                    console.error(`${test}: Test timeout expired`)
                    process.kill()
                }, timeout * 1000)
            }
        } catch (err) {
            console.error(`${test}: Test failed to execute - ${err}`)

            let result = {
                success: false,
                message: "Test failed to execute"
            }

            return res.json(result)
        }
    }

    if (token) {
        app.post("/examiner/test/:test", async function (req, res, next) {
            let request_token = req.query.token

            if (!request_token || request_token != token)
                return next()

            return await examiner_test(req, res, next)
        })
    }
    else {
        app.post("/examiner/test/:test", examiner_test)
    }
}
