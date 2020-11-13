Presenter Slides
================

If a workshop includes a presentation, slides can be included by placing them in the ``workshop/slides`` directory. Anything in this directory will be served up as static files via a HTTP web server. The default web page should be provided as ``index.html``.

Using reveal.js presentation tool
---------------------------------

To support the use of [reveal.js](https://revealjs.com/), static media assets for that package are already bundled and available at the standard URL paths that the package expects. You should therefore be able to drop your slide presentation using reveal.js into the ``workshop/slides`` directory and it will work with no additional setup.

If you are using reveal.js for the slides and you have history enabled, or are using section IDs to support named links, you can use an anchor to a specific slide and that slide will be opened when clicked on:

```text
%slides_url%#/questions
```

When using embedded links to the slides in workshop content, if the workshop content is displayed as part of the dashboard, the slides will be opened in the tab to the right rather than as a separate browser window or tab.

Using a PDF file for presenter slides
-------------------------------------

For slides bundled as a PDF file, add the PDF file to ``workshop/slides`` and then add an ``index.html`` which displays the PDF [embedded](https://stackoverflow.com/questions/291813/recommended-way-to-embed-pdf-in-html) in the page.
