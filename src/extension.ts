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

function showEditor(file : string) : Thenable<vscode.TextEditor> {
    return vscode.workspace.openTextDocument(file)
    .then(doc => {
        log("Opened document");
        //TODO: select line? How?
        return vscode.window.showTextDocument(doc)
    });
}

function pasteAtLine(editor : vscode.TextEditor, line : number, paste : string) : Thenable<any> {
    return editor.edit(editBuilder => {
        const loc = new vscode.Position(line, 0);
        editBuilder.insert(loc, paste);
    })
    .then(editApplies => gotoLine(editor, line));
}

function gotoLine(editor : vscode.TextEditor, line : number) : void {
    let lineStart = new vscode.Position(line, 0);
    let sel = new vscode.Selection(lineStart, lineStart);
    log("Setting selection");
    editor.selection = sel;
    log("Revealing selection");
    editor.revealRange(editor.selection);
}

function findLine(editor : vscode.TextEditor, textOnLine : string) : number {
    textOnLine = textOnLine.trim(); //ignore trailing and leading whitespace
    const lines = editor.document.lineCount
    for (let line = 0; line < lines; line++) {
        let currentLine = editor.document.lineAt(line);
        if (currentLine.text.includes(textOnLine)) {
            return line;
        }
    }
    return lines-1; // pretend we found the snippet on the last line. 
            // pasting there is probably better than just dropping the paste text silently.
}

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

    log('Activating eduk8s-vscode-helper');

    const port = process.env.EDUK8S_VSCODE_HELPER_PORT || 10011;

    const app: express.Application = express();

    app.get("/hello", (req, res) => {
        res.send('Hello World V2 with paste!\n');
        const pre = req.query.pre;
    });

    app.get('/editor/paste', (req, res) => {
        const file = req.query.file as string;
        const pre = req.query.prefix as string;
        const lineStr = req.query.line as string;
        const paste = req.query.paste as string;

        log('Requesting to open:');
        log(` file = ${file}`);
        log(`  pre = ${pre}`);
        log(` line = ${lineStr}`);
        log(`paste = ${paste}`);

        showEditor(file)
        .then(editor => {
            if (lineStr) {
                return pasteAtLine(editor, +lineStr-1, paste);
            } else if (pre) {
                const line = findLine(editor, pre);
                if (line>=0) {
                    //paste it on the *next* line after the found line
                    return pasteAtLine(editor, line+1, paste);
                }
            }
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

    //TODO: change to a 'put' or 'update' request?
    app.get('/editor/line', (req, res) => {
        const file : string  = req.query.file as string;
        const lineStr = req.query.line as string || 1;
        const line = +lineStr-1;
        log('Requesting to open:');
        log(`  file = ${file}`);
        log(`  line = ${line}`);
        showEditor(file)
        .then(editor => {
            log("Showed document");
            gotoLine(editor, line);
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