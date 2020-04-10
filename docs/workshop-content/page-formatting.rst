Page Formatting
===============

Individual module files can use either `Markdown <https://github.github.com/gfm/>`_ or `AsciiDoc <http://asciidoc.org/>`_ markup formats. The extension used on the file should be ``.md`` or ``.adoc``, corresponding to which formatting markup style you want to use.

Annotation of executable commands
---------------------------------

In conjunction with the standard Markdown and AsciiDoc, additional annotations can be applied to code blocks. The annotations are used to indicate that a user can click on the code block and have it copied to the terminal and executed, or copy the code block into the paste buffer so it can be pasted into another window.

If using Markdown, to annotate a code block so that it will be copied to the terminal and executed, use:

.. code-block:: text

    ```execute
    echo "Execute command."
    ```

When you click on the code block the command will be executed in the first terminal of the workshop dashboard.

If using AsciiDoc, you would instead use the ``role`` annotation in an existing code block:

.. code-block:: text

    [source,bash,role=execute]
    ----
    echo "Execute command."
    ----

When the workshop dashboard is configured to display multiple terminals, you can qualify which terminal the command should be executed in by adding a suffix to the ``execute`` annotation. For the first terminal use ``execute-1``, for the second terminal ``execute-2``, etc:

.. code-block:: text

    ```execute-1
    echo "Execute command."
    ```

    ```execute-2
    echo "Execute command."
    ```

In most cases, a command you execute would complete straight away. If you need to run a command that never returns, with the user needing to interrupt it to stop it, you can use the special string ``<ctrl+c>`` in a subsequent code block.

.. code-block:: text

    ```execute
    <ctrl+c>
    ```

When the user clicks on this code block, the running command in the corresponding terminal will be interrupted.

Annotation of text to be copied
-------------------------------

Instead of executing a command, you wanted the content of the code block to be copied into the paste buffer, you can use:

.. code-block:: text

    ```copy
    echo "Text to copy."
    ```

After clicking on this code block, you could then paste the content into another window.

If you have a situation where the text being copied should be modified before use, you can denote this special case by using ``copy-and-edit`` instead of ``copy``. The text will still be copied to the paste buffer, but will be displayed in the browser in a way to highlight that it needs to be changed before use.

.. code-block:: text

    ```copy-and-edit
    echo "Text to copy and edit."
    ```

For AsciiDoc, similar to ``execute``, you can add the ``role`` of ``copy`` or ``copy-and-edit``:

.. code-block:: text

    [source,bash,role=copy]
    ----
    echo "Text to copy."
    ----

    [source,bash,role=copy-and-edit]
    ----
    echo "Text to copy and edit."
    ----

Interpolation of data variables
-------------------------------

When creating page content, you can reference a number of pre-defined data variables. The values of the data variables will be substituted into the page when rendered in the users browser.

The workshop environment provides the following built-in data variables.

* ``workshop_namespace`` - The name of the namespace used for the workshop environment.
* ``session_namespace`` - The name of the namespace the workshop instance is linked to and into which any deployed applications will run.
* ``ingress_domain`` - The host domain which should be used in the any generated hostname of ingress routes for exposing applications.
* ``ingress_protocol`` - The protocol (http/https) that is used for ingress routes which are created for workshops.
* ``base_url`` - The root URL path for the workshop content.
* ``terminal_url`` - The root URL path for the terminal application.
* ``console_url`` - The root URL path for the embedded web console. Only available when using the Kubernetes dashboard as console.
* ``slides_url`` - The root URL path for slides if provided.

To use a data variable within the page content, surround it by matching pairs of brackets:

.. code-block:: text

    {{ session_namespace }}

This can be done inside of code blocks, as well as in URLs:

.. code-block:: text

    http://myapp-{{ session_namespace }}.{{ ingress_domain }}

Note that an older version of the rendering engine required that data variables be surrounded on each side with the character ``%``. This is still supported for backwards compatibility, but you should now use matched pairs of brackets instead. Support for percentage delimiters may be removed in a future version.

You can introduce your own data variables by listing them in the ``workshop/modules.yaml`` file. A data variable is defined as having a default value, but where the value will be overridden if an environment variable of the same name is defined.

The field under which the data variables should be specified is ``config.vars``:

.. code-block:: yaml

    config:
      vars:
      - name: LANGUAGE
        value: undefined

Where you want to use a name for a data variable which is different to the environment variable name, you can add a list of ``aliases``:

.. code-block:: yaml

    config:
      vars:
      - name: LANGUAGE
        value: undefined
        aliases:
        - PROGRAMMING_LANGUAGE

The environment variables with names given in the list of aliases will be checked first, then the environment variable with the same name as the data variable. If no environment variables with those names are set, then the default value will be used.

The default value for a data variable can be overridden for a specific workshop by setting it in the corresponding workshop file. For example, ``workshop/workshop-python.yaml`` might contain:

.. code-block:: yaml

    vars:
      LANGUAGE: python

If you need more control over setting the values of data variables, you can provide the file ``workshop/config.js``. The form of this file should be:

.. code-block:: javascript

    function initialize(workshop) {
        workshop.load_workshop();

        if (process.env['WORKSHOP_FILE'] == 'workshop-python.yaml') {
            workshop.data_variable('LANGUAGE', 'python');
        }
    }

    exports.default = initialize;

    module.exports = exports.default;

This Javascript code will be loaded and the ``initialize()`` function called to load the workshop configuration. You can then use the ``workshop.data_variable()`` function to set up any data variables

Because it is Javascript, you can write any code you need to query process environment variables and set data variables based on those. This might include creating composite values constructed from multiple environment variables. You could even download data variables from a remote host.

Handling of embedded URL links
------------------------------

URLs can be included in workshop content. This can be the literal URL, or the Markdown or AsciiDoc syntax for including and labelling a URL. What happens when a user clicks on a URL, will depend on the specific URL.

In the case of the URL being an external web site, when the URL is clicked, the URL will be opened in a new browser tab or window.

When the URL is a relative page referring to another page which is a part of the workshop content, the page will replace the current workshop page.

You can define a URL where components of the URL are provided by data variables. Data variables useful in this content are ``session_namespace`` and ``ingress_domain`` as they can be used to create a URL to an application deployed from a workshop:

.. code-block:: text

    https://myapp-{{ session_namespace }}.{{ ingress_domain }}

A number of the builtin data variables which provide a URL path value are treated in a special way when used and the user clicks on them.

* ``terminal_url`` - When clicked the terminal tab will be selected and brought to the front if not already visible.
* ``console_url`` - When clicked the console tab will be selected and brought to the front if not already visible. Only available when using the Kubernetes dashboard as console.
* ``slides_url`` - When clicked the slides tab will be selected and brought to the front if not already visible.

In the case of ``terminal_url``, you can append a path to the URL identifying a specific terminal session. In this case a new browser tab or window will be opened on that session:

.. code-block:: text

    {{ terminal_url }}/session/3

In the case of ``console_url``, you can append a path to the URL, and the console tab, as well as being brought to the front if not already visible, will be opened on the given URL path:

.. code-block:: text

    {{ console_url }}/#/overview?namespace={{ session_namespace }}

In the case of ``slides_url``, the slides will be brought to the front if not already visible. If you are using reveal.js for the slides and you have history enabled, or are using section IDs to support named links, you can use an anchor to a specific slide and that specific slide will be opened:

.. code-block:: text

    {{ slides_ur l}}#/questions

Conditional rendering of content
--------------------------------

Rendering of pages is in part handled using the `Liquid <https://www.npmjs.com/package/liquidjs>`_ template engine. You can use any constructs the template engine supports, such as conditional content.

.. code-block:: text

    {% if LANGUAGE == 'java' }
    ....
    {% endif %}
    {% if LANGUAGE == 'python' }
    ....
    {% endif %}
