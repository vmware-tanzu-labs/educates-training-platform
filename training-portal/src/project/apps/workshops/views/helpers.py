"""Helper functions for dealing with URLs."""

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin


def update_query_params(url, params):
    """Update the query parameters of a URL with the given parameters. If the URL
    is malformed or cannot be parsed, the original URL is returned."""

    try:
        # Parse the URL.

        parsed_url = urlparse(url)

        # Handle URLs with no scheme or netloc (e.g., paths like '/page').

        if not parsed_url.scheme and not parsed_url.netloc:
            # Treat it as a relative path URL.

            base_url = "http://dummy"  # Temporary base for relative path handling
            parsed_url = urlparse(urljoin(base_url, url))

        # Parse existing query parameters.

        query_params = parse_qs(parsed_url.query)

        # Update or add the new parameters.

        query_params.update({key: [value] for key, value in params.items()})

        # Reconstruct the URL with the updated query string.

        updated_query = urlencode(query_params, doseq=True)
        updated_url = urlunparse(parsed_url._replace(query=updated_query))

        # If the URL was originally a path, strip out the dummy scheme and netloc.

        if parsed_url.scheme == "http" and parsed_url.netloc == "dummy":
            return updated_url.replace("http://dummy", "")

        return updated_url

    except Exception:  # pylint: disable=broad-except
        # In case of any parsing errors, return the original URL.

        return url
