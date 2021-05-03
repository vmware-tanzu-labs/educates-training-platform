import * as vscode from "vscode"
import * as execWithIndices from "regexp-match-indices"

export interface ReplaceTextSelectionParams {
    file: string,
    text: string
}

export async function replaceTextSelection(params: ReplaceTextSelectionParams) {
    // Display the editor window for the target file.

    const editor = await vscode.workspace.openTextDocument(params.file)
        .then(doc => { return vscode.window.showTextDocument(doc) })

    // Bail out if there was no text to match provided.

    if (params.text === undefined)
        return

    editor.edit(builder => builder.replace(editor.selection, params.text))
}
