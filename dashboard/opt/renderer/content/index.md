---
Title: Nothing to See !!!
ExitSign: Restart
---

Sorry, but it seems there is no workshop content available. See the
documentation for more information on how to add your own workshop content.
In the meantime, feel free to play with the various tests below.

#### Standard code block

```
echo "standard code block"
```

#### Click text to execute

```execute-1
echo "execute in terminal 1"
```

```execute-2
echo "execute in terminal 2"
```

```execute
echo "execute in terminal 1"
```

#### Click text to execute (multiline)

```execute-1
echo "execute in terminal 1 (#1)"
echo "execute in terminal 1 (#2)"
```

#### Click text to copy

```copy
echo "copy text to buffer"
```

#### Click text to copy (multiline)

```copy
echo "copy text to buffer (#1)"
echo "copy text to buffer (#2)"
echo "copy text to buffer (#3)"
echo "copy text to buffer (#4)"
```

#### Click text to copy (and edit)

```copy-and-edit
echo "copy text to buffer"
```

#### Interrupt command

```execute
sleep 3600
```

```execute
<ctrl-c>
```

#### Variable interpolation

base_url: %base_url%

console_url: %console_url%

terminal_url: %terminal_url%

slides_url: %slides_url%

username: %username%

project_namespace: %project_namespace%

cluster_subdomain: %cluster_subdomain%

image_registry: %image_registry%

#### Web site links

[External](https://www.openshift.com)

[Internal](%base_url%)

#### Console links

[Projects](%console_url%)

[Status](%console_url%/overview/ns/%project_namespace%)

[Events](%console_url%/k8s/ns/%project_namespace%/events)

[Pods](%console_url%/k8s/ns/%project_namespace%/pods)

#### Terminal links

[Embedded](%terminal_url%)

[Session 1](%terminal_url%/session/1)

[Session 2](%terminal_url%/session/2)
