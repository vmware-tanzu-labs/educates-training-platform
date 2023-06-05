import * as express from "express"
import * as path from "path"
import * as fs from "fs"

const multer = require("multer")

import { config } from "./config"

const upload = multer({ dest: "/tmp/uploads/" })

export function setup_uploads(app: express.Application, token: string = null) {
    if (!config.enable_uploads)
        return

    function single_file(req, res, next) {
        upload.single("file")(req, res, (err) => {
            if (err) {
                console.log("Error uploading file", err)
            }

            if (err instanceof multer.MulterError) {
                return res.status(500).send("FAILED")
            } else if (err) {
                return res.status(500).send("FAILED")
            }

            if (req.file === undefined) {
                console.log("No file found in upload")
                return res.status(400).send("FAILED")
            }

            if (req.body["path"] === undefined) {
                console.log("No path found in upload")
                return res.status(400).send("FAILED")
            }

            if (!req.body["path"]) {
                console.log("Invalid path found in upload")
                return res.status(400).send("FAILED")
            }

            let pathname = req.body["path"]
            let dirname = path.dirname(pathname)
            let basename = path.basename(pathname)

            if (dirname.startsWith("/")) {
                console.log("Upload path cannot be asbsolute")
                return res.status(500).send("FAILED")
            }

            if (!basename) {
                console.log("Invalid upload path name")
                return res.status(400).send("FAILED")
            }

            dirname = path.join(config.uploads_dir, dirname)

            if (!dirname.startsWith(config.uploads_dir)) {
                console.log("Upload directory context invalid")
                return res.status(400).send("FAILED")
            }

            if (!fs.existsSync(dirname)) {
                fs.mkdirSync(dirname, { recursive: true });
            }

            let old_path = req.file["path"]
            let new_path = path.join(dirname, basename)

            console.log(`Moving upload "${old_path}" to "${new_path}"`)

            try {
                fs.renameSync(old_path, new_path)
            }
            catch (err) {
                console.log("Unable to rename uploaded file", err)
                return res.status(500).send("FAILED")
            }

            return res.status(200).send("OK")
        })
    }

    function multiple_files(req, res, next) {
        upload.array("files")(req, res, (err) => {
            if (err) {
                console.log("Error uploading files", err)
            }

            if (err instanceof multer.MulterError) {
                return res.status(500).send("FAILED")
            } else if (err) {
                return res.status(500).send("FAILED")
            }

            if (req.files === undefined) {
                console.log("No files found in upload")
                return res.status(400).send("FAILED")
            }

            let directory = req.body["directory"] || ""

            if (directory) {
                if (directory.startsWith("/")) {
                    console.log("Upload directory cannot be asbsolute")
                    return res.status(400).send("FAILED")
                }

                directory = path.normalize(path.join(config.uploads_dir, directory))

                if (!directory.startsWith(config.uploads_dir)) {
                    console.log("Upload directory context invalid")
                    return res.status(400).send("FAILED")
                }
            }
            else {
                directory = config.uploads_dir
            }

            if (!fs.existsSync(directory)) {
                fs.mkdirSync(directory, { recursive: true });
            }

            for (let entry of req.files) {
                let old_path = entry["path"]
                let new_path = path.join(directory, entry["originalname"])

                console.log(`Moving upload "${old_path}" to "${new_path}"`)

                try {
                    fs.renameSync(old_path, new_path)
                }
                catch (err) {
                    console.log("Unable to rename uploaded file", err)
                    return res.status(500).send("FAILED")
                }
            }

            return res.status(200).send("OK")
        })
    }

    if (token) {
        app.post("/upload/file", async function (req, res, next) {
            let request_token = req.query.token

            if (!request_token || request_token != token)
                return next()

            return await single_file(req, res, next)
        })

        app.post("/upload/files", async function (req, res, next) {
            let request_token = req.query.token

            if (!request_token || request_token != token)
                return next()

            return await multiple_files(req, res, next)
        })
    }
    else {
        app.post("/upload/file", single_file)
        app.post("/upload/files", multiple_files)
    }
}
