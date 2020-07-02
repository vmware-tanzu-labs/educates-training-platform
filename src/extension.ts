// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import express = require('express');

import * as fs from 'fs';

const log_file_path = "/tmp/eduk8s-vscode-helper.log";


function log(message : string) {
    fs.appendFileSync(log_file_path, message+"\n");
}

log('Loading eduk8s-vscode-helper');

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

    log('Activating eduk8s-vscode-helper');

    const port = process.env.EDUK8S_VSCODE_HELPER_PORT || 10011;

    const app: express.Application = express();

    app.use(function(req, res, next) {
        res.header("Access-Control-Allow-Origin", "*"); // update to match the domain you will make the request from
        // res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
        next();
    });
    app.get("/hello", (req, res) => {
        res.send('Hello World!\n');
    });

    //TODO: change to a a 'put' or 'update' request?
    app.get('/editor/line', (req, res) => {
        const file : string  = req.query.file as string;
        const line = req.query.line as string;
        log('Requesting to open:');
        log(`  file = ${file}`);
        log(`  line = ${line}`);
        vscode.workspace.openTextDocument(file)
        .then(doc => {
            log("Opened document");
            //TODO: select line? How?
            return vscode.window.showTextDocument(doc)
        })
        .then(editor => {
            log("Showed document");
            let lineStart = new vscode.Position(+line, 0);
            let sel = new vscode.Selection(lineStart, lineStart);
            log("Setting selection");
            editor.selection = sel;
            log("Revealing selection");
            editor.revealRange(editor.selection);
        })
        .then(
            () => {
                log("Sending http ok response");
                res.send('OK\n')
            },
            (error) => {
                console.error('Error handling request for '+req.url, error);
                log("Sending http ERROR response");
                res.status(500).send('FAIL\n');
            }
        );
    });

    let server = app.listen(port, () => {
        log(`Eduk8s helper is listening on port ${port}`);
    });

    server.on('error', e => {
        console.error('Problem starting server. Port in use?');
    });

    context.subscriptions.push({dispose: () => server.close()});
}

// this method is called when your extension is deactivated
export function deactivate() {}
