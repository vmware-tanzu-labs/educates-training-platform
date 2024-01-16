import * as express from "express"
import * as child_process from "child_process"
import * as path from "path"
import * as fs from "fs"
import * as os from "os"

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

            process = child_process.spawn(pathname, args, { cwd: os.homedir() })

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
                    process.stdin.on('error', (error) => console.log(`${test}: Error writing to stdin - ${error}`));
                    process.stdin.write(JSON.stringify(form))
                }

                process.stdin.end()
            })

            // Capture examiner script output to a log file.

            const logFilePath = path.join(os.homedir(), ".local/share/workshop/examiner-scripts.log")
            const logStream = fs.createWriteStream(logFilePath, { flags: "a" });

            logStream.on('error', (err) => {
                // Ignore the error to prevent EPIPE error when writing data.
            });

            process.stdout.on('data', (data) => {
                const lines = data.toString().split('\n');
                lines.forEach((line) => {
                    const logData = `${test}: ${line}`;
                    console.log(logData);
                    logStream.write(logData+'\n'); // Append stdout to the log file.
                });
            });

            process.stderr.on('data', (data) => {
                const lines = data.toString().split('\n');
                lines.forEach((line) => {
                    const logData = `${test}: ${line}`;
                    console.log(logData);
                    logStream.write(logData+'\n'); // Append stderr to the log file.
                });
            });

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
