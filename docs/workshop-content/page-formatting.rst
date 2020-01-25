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

When the workshop dashboard is configured to display multiple terminals (the default is two terminals), you can qualify which terminal the command should be executed in by adding a suffix to the ``execute`` annotation. For the first terminal use ``execute-1``, for the second terminal ``execute-2``, etc:

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
* ``base_url`` - The root URL path for the workshop content.
* ``terminal_url`` - The root URL path for the terminal application.
* ``console_url`` - The root URL path for the embedded web console.
* ``slides_url`` - The root URL path for slides if provided.

To use a data variable within the page content, surround it each side with the character ``%``:

.. code-block:: text

    %session_namespace%

This can be done inside of code blocks, as well as in URLs:

.. code-block:: text

    http://myapp-%session_namespace%.%ingress_domain%

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

Enabling the Liquid template engine
-----------------------------------

All content in a page will be displayed. If you need to have content which should only be displayed if certain data variables are set, or need to be able to use some other type of conditional logic, you can optionally enable use of the `Liquid <https://www.npmjs.com/package/liquidjs>`_ template engine.

To enable this, add the ``config.template_engine`` field to the modules configuration file:

.. code-block:: yaml

    config:
        template_engine: liquid.js

This will allow you to use the syntax implemented by the Liquid template engine:

.. code-block:: text

    {% if LANGUAGE == 'java' }
    ....
    {% endif %}
    {% if LANGUAGE == 'python' }
    ....
    {% endif %}

Note that when enabling the template engine, the way you make use of data variables changes.

Instead of use the ``%`` character to enclose the name of the data variable you want inserted, you need to use the Liquid convention for referencing data variables. That is, ``{{ LANGUAGE }}``.
