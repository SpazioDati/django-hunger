from django import forms
from django.utils.translation import ugettext_lazy as _
from hunger.models import InvitationCode

class InviteRequestForm(forms.ModelForm):
    class Meta:
        model = InvitationCode
        fields = ['email']
        widgets = {"email": forms.TextInput({"placeholder": "Enter your email"}), }


class InvitationEmailForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea,
        help_text=_('Also accepts HTML code. The text "{invite_url}" is '
                    'a placeholder for the actual invitation url.'),
        required=False
    )
