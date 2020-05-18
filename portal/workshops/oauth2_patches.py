import fnmatch

from urllib.parse import parse_qsl
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import wrapt

# This mess is to add functionality to Django auth toolkit to allow
# wildcards in accepted URIs for OAuth clients. You are supposed to be
# able to do this via the Django auth toolkit pluggable Application
# model, but that appears to be impossible to use for a fresh
# application from the outset when the database doesn't exist. Instead
# it relies on manually applied migrations in step with making changes
# to the Django settings file. Can't find any way of automating that
# process properly and so only other choice was to monkey patch the
# Django auth toolkit Application object to add the required checks.

def validate_uris(value):
    # Ensure that value is a space separated list of URIs. Note that
    # components of the host name may be '*'. This shouldn't break
    # urlparse() function though.

    from oauth2_provider.settings import oauth2_settings

    urls = value.split()

    for url in urls:
        obj = urlparse(url)
        if obj.fragment:
            raise ValidationError('Redirect URIs must not contain fragments')
        if obj.scheme.lower() not in oauth2_settings.ALLOWED_REDIRECT_URI_SCHEMES:
            raise ValidationError('Redirect URI scheme is not allowed.')
        if not obj.netloc:
            raise ValidationError('Redirect URI must contain a domain.')

def uri_is_allowed(uri, allowed_uri):
    # Validate the URI against a single expected match. The host name
    # (netloc) can contain a glob style wildcard ('*') such that it can
    # match against sub domains.

    schemes_match = uri.scheme == allowed_uri.scheme
    netloc_matches_pattern = fnmatch.fnmatch(uri.netloc, allowed_uri.netloc)
    paths_match = uri.path == allowed_uri.path

    return all([schemes_match, netloc_matches_pattern, paths_match])

def wrapper_Application_redirect_uri_allowed(wrapped, instance, args, kwargs):
    # Validate the URI against all possible matches. We only consider
    # the scheme, host name and path. We don't care about query string
    # arguments. The host name (netloc) can contain a glob style
    # wildcard ('*') such that it can match against sub domains.

    def _args(uri):
        return uri

    self = instance
    uri = _args(*args, **kwargs)

    parsed_uri = urlparse(uri)

    for allowed_uri in self.redirect_uris.split():
        parsed_allowed_uri = urlparse(allowed_uri)

        if uri_is_allowed(parsed_uri, parsed_allowed_uri):
            return True

    return False

def wrapper_Application_clean(wrapped, instance, args, kwargs):
    # Check inputs when data added. We don't do strict validation
    # of host name as we want to allow glob style wildcard ('*').

    self = instance

    grant_types = (self.GRANT_AUTHORIZATION_CODE, self.GRANT_IMPLICIT)

    redirect_uris = self.redirect_uris.strip().split()
    allowed_schemes = set(s.lower() for s in self.get_allowed_schemes())

    if redirect_uris:
        for uri in redirect_uris:
            scheme = urlparse(uri).scheme
            if scheme not in allowed_schemes:
                raise ValidationError(_(
                    "Unauthorized redirect scheme: {scheme}"
                ).format(scheme=scheme))

    elif self.authorization_grant_type in grant_types:
        raise ValidationError(_(
            "redirect_uris cannot be empty with grant_type {grant_type}"
        ).format(grant_type=self.authorization_grant_type))

def wrapper_Application___init__(wrapped, instance, args, kwargs):
    # Override default validator for redirect URIs field as it is too
    # strict. We need to allow wildcard in the host name.

    instance._meta.get_field('redirect_uris').validators = [validate_uris, ]

    # Call the original base class constructor.

    wrapped(*args, **kwargs)

    # Replace specific methods of the class used to validate URI and
    # check inputs when entering data for redirect URIs.

    wrapt.wrap_function_wrapper(instance, 'redirect_uri_allowed',
            wrapper_Application_redirect_uri_allowed)
    wrapt.wrap_function_wrapper(instance, 'clean',
            wrapper_Application_clean)


# We need to delay patch of code until the point that the module is imported
# else we end up with problem that Django will not have been initialised.

def patch_oauth2_provider_model(module):
    wrapt.wrap_function_wrapper(module, 'Application.__init__',
            wrapper_Application___init__)

wrapt.register_post_import_hook(patch_oauth2_provider_model,
        'oauth2_provider.models')
