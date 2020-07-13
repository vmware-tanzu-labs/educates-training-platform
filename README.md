# eduk8s-vscode-helper README

The 'eduk8s-vscode-helper' is an extension that provides the means for the 'eduk8s' environment
to 'ask' the embedded editor to do certain things, such as... opening a file on a given line, 
pasting text into the editor etc. 

## Usage

### Open file on line

To ask the editor to open a file on a given line:

```
curl "localhost:10011/editor/line?file=/home/kdvolder/git/kdvolder/hello-boot/src/main/java/com/example/demo/PathConstants.java&line=2"
```

Note: line numbers start now start at 1 (this is different from vscode api, but more logical to users).

### Paste text into a file

Two different uses are supported. You can either identify the location where text is to be pasted as a 
line number:

```
curl 'http://localhost:10011/editor/paste?file=...path...&line=...number...&paste=...text...'
```

Alternatively you identify the insert location as a snippet of text. The text is searched for and paste
snippet will be inserted just after the line where that snippet is found, or at the end of the document
if it is not found.

```
curl 'http://localhost:10011/editor/paste?file=...path...&prefix=...searchString...&paste=...text...'
```

Caveats and limitations:

- if the search text is not found, text is pasted at the end of the document.
- search text cannot span more than one line.
- if there is more than one occurrence only the first one is considered.

## Extension Settings

You can change the port on which the extension listens by setting the `EDUK8S_VSCODE_HELPER_PORT` environment variable.

## Building 

```
git clone https://github.com/kdvolder/eduk8s-vscode-helper.git
cd eduk8s-vscode-helper
npm run vsce-package
```

The resulting vsix file will be in the root directorty of the project.
