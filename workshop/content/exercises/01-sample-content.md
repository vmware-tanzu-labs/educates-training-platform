This is an example page for exercises to be done for the workshop. You would remove this page, replace it with your own and then adjust the `workshop.yaml` and `modules.yaml` file to list your pages instead.

In this example the pages which make up the core of the workshop content are placed in a sub directory. This is only done as a suggestion. You can place all pages at the same directory level if you wish.

Included below are some tests and examples of page formatting using Markdown.

#### Standard code block

```
echo "standard code block"
```

#### Click text to execute

```execute
echo "execute in terminal 1"
```

```execute-1
echo "execute in terminal 1 (annotated)"
```

```execute-2
echo "execute in terminal 2 (annotated)"
```

#### Click text to copy

```copy
echo "copy text to buffer"
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

base_url: {{ base_url }}

console_url: {{ console_url }}

terminal_url: {{ terminal_url }}

slides_url: {{ slides_url }}

workshop_namespace: {{ workshop_namespace }}

session_namespace: {{ session_namespace }}

ingress_domain: {{ ingress_domain }}

#### Web site links

[External](https://github.com/eduk8s)

[Internal]({{ base_url }})

#### Console links

[Namespace]({{ console_url }}/#/overview?namespace={{ session_namespace }})

#### Terminal links

[Embedded]({{ terminal_url }})

[Session 1]({{ terminal_url }}/session/1)

[Session 2]({{ terminal_url }}/session/2)
