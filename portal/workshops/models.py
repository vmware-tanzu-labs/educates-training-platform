from django.db import models
from django.contrib.auth.models import User

import re
from urllib.parse import parse_qsl
from urllib.parse import urlparse
from django.core.exceptions import ValidationError
from oauth2_provider.models import AbstractApplication
from oauth2_provider.settings import oauth2_settings

class Workshop(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    vendor = models.CharField(max_length=256)
    title = models.CharField(max_length=256)
    description = models.TextField(max_length=1024)
    url = models.CharField(max_length=512)

class Session(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    id = models.CharField(max_length=64)
    hostname = models.CharField(max_length=256)
    secret = models.CharField(max_length=128)
    reserved = models.BooleanField(default=False)
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT)

class Environment(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    workshop = models.ForeignKey(Workshop, on_delete=models.PROTECT)
    sessions = models.ManyToManyField(Session)

def validate_uris(value):
    """Ensure that `value` contains valid blank-separated URIs."""
    urls = value.split()
    for url in urls:
        obj = urlparse(url)
        if obj.fragment:
            raise ValidationError('Redirect URIs must not contain fragments')
        if obj.scheme.lower() not in oauth2_settings.ALLOWED_REDIRECT_URI_SCHEMES:
            raise ValidationError('Redirect URI scheme is not allowed.')
        if not obj.netloc:
            raise ValidationError('Redirect URI must contain a domain.')

class Application(AbstractApplication):
    """Subclass of application to allow for regular expressions for the redirect uri."""

    @staticmethod
    def _uri_is_allowed(allowed_uri, uri):
        """Check that the URI conforms to these rules."""
        schemes_match = allowed_uri.scheme == uri.scheme
        netloc_matches_pattern = re.fullmatch(allowed_uri.netloc, uri.netloc)
        paths_match = allowed_uri.path == uri.path

        return all([schemes_match, netloc_matches_pattern, paths_match])

    def __init__(self, *args, **kwargs):
        """Relax the validator to allow for uris with regular expressions."""
        self._meta.get_field('redirect_uris').validators = [validate_uris, ]
        super(). __init__(*args, **kwargs)

    def redirect_uri_allowed(self, uri):
        """
        Check if given url is one of the items in :attr:`redirect_uris` string.
        A Redirect uri domain may be a regular expression e.g. `^(.*).example.com$` will
        match all subdomains of example.com.
        A Redirect uri may be `https://(.*).example.com/some/path/?q=x`
        :param uri: Url to check
        """
        for allowed_uri in self.redirect_uris.split():
            parsed_allowed_uri = urlparse(allowed_uri)
            parsed_uri = urlparse(uri)

            if self._uri_is_allowed(parsed_allowed_uri, parsed_uri):
                aqs_set = set(parse_qsl(parsed_allowed_uri.query))
                uqs_set = set(parse_qsl(parsed_uri.query))

                if aqs_set.issubset(uqs_set):
                    return True

        return False
