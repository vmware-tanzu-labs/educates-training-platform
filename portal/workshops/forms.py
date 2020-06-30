from django import forms

class AccessTokenForm(forms.Form):
    password = forms.CharField(label='Password', max_length=64, required=True)
    redirect_url = forms.CharField(widget=forms.HiddenInput(), required=True)
