// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import express = require('express');

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
    console.log('Activating eduk8s-vscode-helper');

    const port = process.env.EDUK8S_VSCODE_HELPER_PORT || 10011;

    const app: express.Application = express();

    app.get("/hello", (req, res) => {
        res.send('Hello World!\n');
    });

    //TODO: change to a a 'put' or 'update' request?
    app.get('/editor/line', (req, res) => {
        const file : string  = req.query.file as string;
        const line = req.query.line as string;
        console.log('Requesting to open:');
        console.log(`  file = ${file}`);
        console.log(`  line = ${line}`);
        vscode.workspace.openTextDocument(file)
        .then(doc => {
            console.log("Opened document");
            //TODO: select line? How?
            return vscode.window.showTextDocument(doc)
        })
        .then(editor => {
            console.log("Showed document");
            let lineStart = new vscode.Position(+line, 0);
            let sel = new vscode.Selection(lineStart, lineStart);
            console.log("Setting selection");
            editor.selection = sel;
            console.log("Revealing selection");
            editor.revealRange(editor.selection);
        })
        .then(
            () => {
                console.log("Sending http ok response");
                res.send('OK\n')
            },
            (error) => {
                console.error('Error handling request for '+req.url, error);
                console.log("Sending http ERROR response");
                res.status(500).send('FAIL\n');
            }
        );
    });

    let server = app.listen(port, () => {
        console.log(`Eduk8s helper is listening on port ${port}`);
    });

    server.on('error', e => {
        console.error('Problem starting server. Port in use?');
    });

    context.subscriptions.push({dispose: () => server.close()});
}

// this method is called when your extension is deactivated
export function deactivate() {}
