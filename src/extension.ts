// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import express = require('express');
import * as fs from 'fs';

import * as yaml from 'yaml';
import { Node, YAMLMap } from 'yaml/types';
import { O_DIRECT } from 'constants';
import { stringify } from 'querystring';

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

function exists(file: string) : Promise<boolean> {
    return new Promise((resolve, reject) => {
        fs.access(file, fs.constants.F_OK, (err) => {
            resolve(err ? false : true);
        });
    });
}

function createFile(file : string, content : string) : Promise<any> {
    return new Promise((resolve, reject) => {
        fs.writeFile(file, content, (err) => {
            if (err) {
                reject(err);
            } else {
                resolve();
            }
        });
    });
}

async function pasteAtYamlPath(file: string, yamlPath: string, paste: string) : Promise<any> {
    let editor = await showEditor(file);
    let text = editor.document.getText();
    let opts : yaml.Options = {
    };
    //TODO: deal with multi docs properly. For now we just assume one document.
    let doc = yaml.parseAllDocuments(text, opts)[0];
    let target = findNode(doc, yamlPath);
    log("Found target node with range: "+target?.range);
    let offset = target?.range?.[0];
    if (offset) {
        let pos = editor.document.positionAt(offset);
        let indent = " ".repeat(pos.character);
        if (indent) {
            paste = indent + paste.trim().replace(new RegExp('\n','g'), '\n'+indent) + '\n'; 
        }
        return pasteAtLine(editor, pos.line, paste);
    }
}

function findNode(doc : yaml.Document.Parsed, path : string) : Node | null {
    if (doc.contents) {
        return navigate(doc.contents, path);
    }
    return null;
}

function navigate(node : Node, path : string) : Node {
    if (!path) {
        return node;
    } else {
        if (path[0]==='[') {
            //TODO: array navigation
        } else {
            let head = parsePath(path);
            if (head.key) {
                let tp = node.type;
                if (node.type === 'MAP') {
                    let map = node as YAMLMap;
                    let val = map.get(head.key);
                    return navigate(val, head.tail);
                } else {
                    throw "Key not found: "+head.key;
                }
            }
            if (head.index) {
                throw "Yaml pathing into sequence nodes not yet implemented";
            }
        }
    }
    throw "Invalid yaml path";
}

interface Path {
    key ?: string,
    index ?: number,
    tail: string
}

function parsePath(path : string) : Path {
    if (path[0]==='[') {
        let closeBracket = path.indexOf(']');
        if (closeBracket>=0) {
            return {
                index: parseInt(path.substring(1, closeBracket)),
                tail: path.substring(closeBracket+1)
            };
        }
    } else {
        let dot = path.indexOf('.');
        if (dot>=0) {
            return {
                key: path.substring(0, dot),
                tail: path.substring(dot+1)
            };
        } else {
            return { 
                key: path,
                tail: ""
            };
        }
    }
    throw "invalid yaml path syntax";
}

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

    log('Activating eduk8s-vscode-helper');

    const port = process.env.EDUK8S_VSCODE_HELPER_PORT || 10011;

    const app: express.Application = express();

    app.get("/hello", (req, res) => {
        res.send('Hello World V4 with paste into new file!\n');
        const pre = req.query.pre;
    });

    let commandInProgress = false;
    app.get('/command/:id', (req, res) => {
        if (commandInProgress) {
            res.send("SKIPPED");
        } else {
            commandInProgress = true;
            vscode.commands.executeCommand(req.params.id).then(
                () => {
                    log("Sending http ok response");
                    commandInProgress = false;
                    res.send('OK\n');
                },
                (error) => {
                    console.error('Error handling request for '+req.url, error);
                    log("Sending http ERROR response");
                    commandInProgress = false;
                    res.status(500).send('FAIL\n');
                }
            );
            }
    });

    app.get('/editor/paste', (req, res) => {

        const file = req.query.file as string;
        const pre = req.query.prefix as string;
        const lineStr = req.query.line as string;
        const yamlPath = req.query.yamlPath as string;
        let paste = req.query.paste as string;
        if (!paste.endsWith("\n")) {
            log("Adding missing newline terminator to paste string");
            paste+="\n";
        }

        log('Requesting to paste:');
        log(` file = ${file}`);
        log(`  pre = ${pre}`);
        log(` line = ${lineStr}`);
        log(`paste = ${paste}`);
        log(` yamlPath = ${yamlPath}`);

        exists(file)
        .then((ex) => {
            if (ex) {
                log("File exists");
                return showEditor(file)
                .then(editor => {
                    if (yamlPath) {
                        return pasteAtYamlPath(file, yamlPath, paste);
                    } else if (lineStr) {
                        return pasteAtLine(editor, +lineStr-1, paste);
                    } else if (pre) {
                        const line = findLine(editor, pre);
                        if (line>=0) {
                            //paste it on the *next* line after the found line
                            return pasteAtLine(editor, line+1, paste);
                        }
                    }
                });
            } else {
                log("File does not exist");
                createFile(file, paste)
                .then(x => {
                    log("Created file");
                    return showEditor(file);
                });
            }
        })
        .then(
            () => {
                log("Sending http ok response");
                res.send('OK\n');
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