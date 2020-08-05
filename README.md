# eduk8s-vscode-helper

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

## Building for Testing

To build locally, run:

```
git clone https://github.com/kdvolder/eduk8s-vscode-helper.git
cd eduk8s-vscode-helper
npm install
npm run vsce-package
```

The resulting vsix file will be in the root directorty of the project and can be loaded with a local VS Code editor.

To test in conjunction with the ``code-server`` variant of VS Code used with eduk8s, build a container image by running:

```
docker build -t eduk8s-vscode-helper .
```

Then run:

```
docker run --rm -p 10085:10085 eduk8s-vscode-helper:latest
```

Open the browser on ``http://localhost:10085``.

From the browser based editor, open ``test-helper.http`` to then manually trigger tests.

## Automated Builds

When changes are pushed back up to GitHub, a container image will be automatically built and published to quay.io.

Tagged versions of the container images can be found at:

* https://quay.io/repository/eduk8s/eduk8s-vscode-helper?tab=tags

Any new development work must be done on the ``develop`` branch and if built version of the container image is required to test, changes must first be pushed up to GitHub on the ``develop`` branch.

Only merge from ``develop`` branch to ``master`` branch when the changes are all confirmed working.

When a merge is done to ``master``, this will trigger a GitHub action to tag a release with version string constructed from date/time and commit hash. This is why you must work in ``develop`` branch, otherwise if you work in ``master`` branch, every time you push back changes you will trigger a new tagged release and it will not be possible to know what are valid releases which are tested and accepted.

Note that as a fail safe for when ``quay.io`` is experiencing a major outage, you can also obtain the container image from:

* https://github.com/eduk8s/images/packages/343313

Using container images from GitHub requires though you have credentials to login to GitHub. To get these you would need to create a personal access token for use over HTTP.

## Using Compiled Extension

The compiled extension will be pulled into the base workshop images from a ``Dockerfile`` using something similar to:

```
FROM quay.io/eduk8s/eduk8s-vscode-helper:200805.030856.587d3ba AS vscode-helper

FROM ...

COPY --chown=1001:0 --from=vscode-helper /opt/eduk8s/workshop/code-server/extensions/. /opt/code-server/extensions/
```

This will always use a specific tagged version.

If you want to test with a ``develop`` version, then you can in a custom workshop image use:

```
FROM quay.io/eduk8s/eduk8s-vscode-helper:develop AS vscode-helper

FROM quay.io/base-environment:master

COPY --chown=1001:0 --from=vscode-helper /opt/eduk8s/workshop/code-server/extensions/. /opt/code-server/extensions/
```

or if for some reason you need to be able to install it from a ``vsix`` file, use:

```
FROM quay.io/eduk8s/eduk8s-vscode-helper:develop AS vscode-helper

FROM quay.io/base-environment:master

COPY --chown=1001:0 --from=vscode-helper /home/eduk8s/eduk8s-vscode-helper-0.0.1.vsix /home/eduk8s/

RUN code-server --install-extension eduk8s-vscode-helper-0.0.1.vsix && \
    rm eduk8s-vscode-helper-0.0.1.vsix
```

This latter method presumes that the extension version has been updated in ``package.json`` and is different for the newer version, else it will not be installed since the version will be the same as the original one in the base workshop image.

Since it is always the ``develop`` tag and ``docker`` will cache the container image locally, you will have to force pull an updated remote image with same tag name, or tell ``docker`` to ignore the local cache when building, else it will use whatever you have locally and not use the updated remote version.
