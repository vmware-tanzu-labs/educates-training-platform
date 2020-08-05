// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import express = require('express');
import { Request, Response } from 'express-serve-static-core';
import * as fs from 'fs';
import * as bodyParser from 'body-parser';

import * as yaml from 'yaml';
import { Node, YAMLMap } from 'yaml/types';

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
    log(`called pasteAtLine(${line})`);
    return editor.edit(editBuilder => {
        const loc = new vscode.Position(line, 0);
        editBuilder.insert(loc, paste);
    })
    .then(editApplies => gotoLine(editor, line));
}

function gotoLine(editor : vscode.TextEditor, line : number) : void {
    log(`called gotoLine(${line})`);
    let lineStart = new vscode.Position(line, 0);
    let sel = new vscode.Selection(lineStart, lineStart);
    log("Setting selection");
    editor.selection = sel;
    log("Revealing selection");
    editor.revealRange(editor.selection);
}

function findLine(editor : vscode.TextEditor, textOnLine : string) : number {
    textOnLine = textOnLine.trim(); //ignore trailing and leading whitespace
    const lines = editor.document.lineCount;
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
                    throw new Error("Key not found: "+head.key);
                }
            }
            if (head.index) {
                throw new Error("Yaml pathing into sequence nodes not yet implemented");
            }
        }
    }
    throw new Error("Invalid yaml path");
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
    throw new Error("invalid yaml path syntax");
}

interface PasteParams {
    file: string;
    prefix?: string;
    lineNumber?: number;
    paste: string;
    yamlPath?: string;
}

async function handlePaste(params: PasteParams) {
    if (typeof params.lineNumber === 'number') {
        params.lineNumber--;
    }

    if (!params.paste.endsWith("\n")) {
        log("Adding missing newline terminator to paste string");
        params.paste+="\n";
    }

    log('Requesting to paste:');
    log(` file = ${params.file}`);
    log(`  pre = ${params.prefix}`);
    log(` line = ${params.lineNumber}`);
    log(`paste = ${params.paste}`);
    log(` yamlPath = ${params.yamlPath}`);

    if (await exists(params.file)) {
        log(`File '${params.file}' exists`);
        const editor = await showEditor(params.file);

        log("Editor shown");
        if (params.yamlPath) {
            log("Paste at yaml codepath");
            return await pasteAtYamlPath(params.file, params.yamlPath, params.paste);
        } else if (typeof params.lineNumber === 'number' && params.lineNumber >= 0) {
            log("Paste at line codepath");
            return await pasteAtLine(editor, params.lineNumber, params.paste);
        } else if (params.prefix) {
            log("Paste at prefix codepath");
            const line = findLine(editor, params.prefix);
            log("line = "+line);
            if (line>=0) {
                //paste it on the *next* line after the found line
                return await pasteAtLine(editor, line+1, params.paste);
            }
        } else {
            pasteAtLine(editor, editor.document.lineCount, params.paste);
        }
    } else {
        log("File does not exist");
        await createFile(params.file, params.paste);
        log("Created file");
        return await showEditor(params.file);
    }
}

interface GoToLineParams {
    file: string;
    line?: number;
}

async function handleGoToLine(params: GoToLineParams) {
    if (typeof params.line === 'number' && params.line > 0) {
        params.line--;
    }
    log('Requesting to open:');
    log(`  file = ${params.file}`);
    log(`  line = ${params.line}`);
    const editor  = await showEditor(params.file);
    log("Showed document");
    if (typeof params.line === 'number' && params.line >= 0) {
        gotoLine(editor, params.line);
    }
}

function createResponse(result: Promise<any>, req: Request<any>, res: Response<any>) {
    res.setHeader('content-type', 'text/plain');
    result.then(() => {
        log("Sending http ok response");
        res.send('OK\n');
    },
    (error) => {
        log(`Error handling request for '${req.url}':  ${error}`);
        log("Sending http ERROR response");
        res.status(500).send('FAIL\n');
    });
}

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

    log('Activating eduk8s-vscode-helper');

    const port = process.env.EDUK8S_VSCODE_HELPER_PORT || 10011;

    const app: express.Application = express();

    app.use(bodyParser.json());

    app.get("/hello", (req, res) => {
        res.send('Hello World V4 with paste into new file!\n');
        const pre = req.query.pre;
    });

    let commandInProgress = false;
    app.post('/command/:id', (req, res) => {
        res.setHeader('content-type', 'text/plain');
        if (commandInProgress) {
            res.status(200).send("SKIPPED");
        } else {
            commandInProgress = true;
            const parameters: any[] = Array.isArray(req.body) ? req.body : [];
            vscode.commands.executeCommand(req.params.id, ...parameters).then(
                () => {
                    log(`Successfully executed command: '${req.params.id}'`);
                    commandInProgress = false;
                },
                (error) => {
                    log(`Failed executing command '${req.params.id}': ${error}`);
                    commandInProgress = false;
                }
            );
            res.status(202).send();
        }
    });

    app.post('/editor/paste', (req, res) => {
        const parameters = req.body || {} as PasteParams;
        createResponse(handlePaste(parameters), req, res);
    });

    app.get('/editor/paste', (req, res) => {
        const parameters: PasteParams = {
            file: req.query.file as string,
            prefix: req.query.prefix as string,
            lineNumber: req.query.line ? parseInt(req.query.line as string) : undefined,
            yamlPath: req.query.yamlPath as string,
            paste: req.query.paste as string
        };
        createResponse(handlePaste(parameters), req, res);
    });

    app.post('/editor/line', (req, res) => {
        const parameters = req.body as GoToLineParams;
        createResponse(handleGoToLine(parameters), req, res);
    });

    //TODO: change to a 'put' or 'update' request?
    app.get('/editor/line', (req, res) => {
        const file : string  = req.query.file as string;
        const line = req.query.line ? parseInt(req.query.line as string) : undefined;

        createResponse(handleGoToLine({
            file,
            line
        }), req, res);
    });

    let server = app.listen(port, () => {
        log(`Eduk8s helper is listening on port ${port}`);
    });

    server.on('error', e => {
        log('Problem starting server. Port in use?');
    });

    context.subscriptions.push({dispose: () => server.close()});
}

// this method is called when your extension is deactivated
export function deactivate() {}