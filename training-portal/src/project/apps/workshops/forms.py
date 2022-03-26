"""Django forms objects.

"""

from django import forms


class AccessTokenForm(forms.Form):
    """Input for used when access token is required to access training portal."""

    password = forms.CharField(
        label="Password", widget=forms.PasswordInput(), max_length=64, required=True
    )
    redirect_url = forms.CharField(widget=forms.HiddenInput(), required=True)
