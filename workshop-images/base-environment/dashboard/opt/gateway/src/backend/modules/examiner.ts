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

export function setup_examiner(app: express.Application) {
    if (!config.enable_examiner)
        return

    app.use("/examiner/test/", express.json());

    app.post("/examiner/test/:test", async function (req, res, next) {
        let test = req.params.test

        let options = req.body

        let timeout = options.timeout || 15
        let args = options.args || []

        if (!test)
            return next()

        let pathname = find_test_program(test)

        if (!pathname)
            return res.sendStatus(404)

        let process: any

        try {
            process = child_process.spawn(pathname, args)
        } catch (err) {
            let result = {
                success: false,
                message: "Test failed to start"
            }

            return res.json(result)
        }

        let timer: any

        if (timeout) {
            console.log(`${test}: timeout=${options.timeout}`)
            timer = setTimeout(() => {
                console.error(`${test}: Test timeout expired`)
                process.kill();
            }, timeout * 1000)
        }

        process.stdout.on('data', (data) => {
            console.log(`${test}: ${data}`)
        });

        process.stderr.on('data', (data) => {
            console.error(`${test}: ${data}`)
        });

        process.on('close', (code) => {
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
    })
}
