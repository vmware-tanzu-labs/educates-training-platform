// Once the document is ready rewrite the URL to remove the query string.

document.addEventListener("DOMContentLoaded", function (event) {
    if (window.location.search) {
        var currentURLWithoutQueryString = window.location.origin + window.location.pathname;
        console.log("Replacing page URL with: " + currentURLWithoutQueryString);
        window.history.replaceState({}, document.title, currentURLWithoutQueryString);
    }
});
