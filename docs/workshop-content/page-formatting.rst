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
