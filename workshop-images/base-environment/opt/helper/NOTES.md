# eduk8s-vscode-helper

The 'eduk8s-vscode-helper' is an extension that provides the means for the 'eduk8s' environment
to 'ask' the embedded editor to do certain things, such as... opening a file on a given line, 
pasting text into the editor etc. 

## Usage

Use 'POST' requests with 'parameters' in json body. GET requests are still
supported but no longer documented. They should no longer be used moving
forward and will eventually be removed.

### Open file

```
POST {{rest_api_host}}/editor/line HTTP/1.1
content-type: application/json

{
    "file": "/home/eduk8s/sample.txt"
}
```

### Open file on line

To ask the editor to open a file on a given line:

```
POST http://localhost:10011/editor/line HTTP/1.1
content-type: application/json

{
    "file": "/home/eduk8s/sample.txt",
    "line": 2
}
```

### Paste text into a file

Several different ways to use this are supported: 

- identify the location where text is to be pasted as a line number
- identify the location where text is to pasted as a search text snippet
- identify the location where text is to be pasted as a 'yaml path' expression (only for yaml files).
- if file does not exist, it is created
- if no location is specified text is pasted at end of the file.

#### Line number:

```
POST {{rest_api_host}}/editor/paste HTTP/1.1
content-type: application/json

{
    "file": "/home/eduk8s/sample.txt",
    "line": 4,
    "paste": "text_at_line_4"
}
```

#### Search snippet:

The editor text is searched for a line of text containing a snippet. 
The text is pasted on the next line.

```
POST http://localhost:10011/editor/paste HTTP/1.1
content-type: application/json

{
    "file": "/home/eduk8s/sample.txt",
    "prefix": "snippet",
    "paste": "text_after_snippet"
}
```

Caveats and limitations:

- if the search text is not found, text is pasted at the end of the document.
- search text cannot span more than one line.
- if there is more than one occurrence only the first one is considered.

#### Yaml Path:

If the target file contains data in yaml format you can indicate the paste location as a 'yamlPath' expression.

```
POST {{rest_api_host}}/editor/paste HTTP/1.1
content-type: application/json

{
    "file": "/home/eduk8s/sample.yml",
    "yamlPath": "spec.template.spec.containers",
    "paste": "- name: otherContainer\n  image: otherimage"
}
```

Pathexpression are composed of 

- property names separated by '.' for navigating into map nodes. 
- `[<number>]` for navigating into sequence nodes (index is 0 based).
- `[<name>=<value>]` for navigaring into sequence picking a node that has a given 
   attribute value.

Some example yamlPath expressions:

- `spec.template.spec.containers[0]` : selects the first container in a typical kubernetes
               deployment manifest.
- `spec.template.spec.containers[name=nginx]`: selects container who's name is `nginx`.
- `spec.template.spec.containers[name=nginx].ports`: selects the `ports` section of the `
   `nginx` container. 

The paste text will be inserted as the end of the selected node and indented to align with
existing children of the node (so that the pasted text becomes a new child of the selected node).

Caveats and limitations:

- pasting assumes 'block' rather than 'flow' syntax at the paste location. Trying to paste 
  text into a 'flow' location is not yet supported and will have unpredictable / incorrect 
  result.
- multi-document yaml files are not yet supported (paste always targets the first 
  'document' in a yaml file implicitly)


#### Paste at end of File

If no location (i.e. no `prefix`, `line` or `yamlPath` ) is specified, then the paste text
is simply appended to the end of the document. A leading newline will be added automatically
to ensure the paste text starts on a new line. 

```
POST {{rest_api_host}}/editor/paste HTTP/1.1
content-type: application/json

{
    "file": "/home/eduk8s/sample.yml",
    "paste": "- name: otherContainer\n  image: otherimage"
}
```

#### Paste into a New file

If the target file does not exist, then it will be created and the paste text is used 
as it's initial contents.

```
POST {{rest_api_host}}/editor/paste HTTP/1.1
content-type: application/json

{
    "file": "/path/to/non-existing-file",
    "paste": "initial contents\nfor the new file"
}
```

## Extension Settings

You can change the port on which the extension listens by setting the `EDUCATES_VSCODE_HELPER_PORT` environment variable.

## Building for Testing

To build locally, run:

```
git clone https://github.com/eduk8s/eduk8s-vscode-helper.git
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

The compiled extension and associated files will be pulled into the base workshop images from a ``Dockerfile`` using something similar to:

```
FROM quay.io/eduk8s/eduk8s-vscode-helper:200805.030856.587d3ba AS vscode-helper

FROM ...

COPY --from=vscode-helper --chown=1001:0 /opt/eduk8s/workshop/code-server/extensions/. /opt/code-server/extensions/

COPY --from=vscode-helper --chown=1001:0 /opt/eduk8s/workshop/gateway/routes/. /opt/eduk8s/workshop/gateway/routes/
```

This will always use a specific tagged version.

If you want to test with a ``develop`` version, then you can in a custom workshop image use:

```
FROM quay.io/eduk8s/eduk8s-vscode-helper:develop AS vscode-helper

FROM quay.io/base-environment:master

COPY --from=vscode-helper --chown=1001:0 /opt/eduk8s/workshop/code-server/extensions/. /opt/code-server/extensions/
```

or if for some reason you need to be able to install it from a ``vsix`` file, use:

```
FROM quay.io/eduk8s/eduk8s-vscode-helper:develop AS vscode-helper

FROM quay.io/base-environment:master

COPY --from=vscode-helper --chown=1001:0 /home/eduk8s/eduk8s-vscode-helper-0.0.1.vsix /home/eduk8s/

RUN code-server --install-extension eduk8s-vscode-helper-0.0.1.vsix && \
    rm eduk8s-vscode-helper-0.0.1.vsix
```

This latter method presumes that the extension version has been updated in ``package.json`` and is different for the newer version, else it will not be installed since the version will be the same as the original one in the base workshop image.

You do not need to copy the routes file into a custom workshop image unless for some reason you had to modify it.

Since it is always the ``develop`` tag and ``docker`` will cache the container image locally, you will have to force pull an updated remote image with same tag name, or tell ``docker`` to ignore the local cache when building, else it will use whatever you have locally and not use the updated remote version.
