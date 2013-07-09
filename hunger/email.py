import os.path
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.template.loader import get_template, render_to_string
from django.template import Context
from hunger.utils import setting, MandrillMail

try:
    from templated_email import send_templated_mail
    templated_email_available = True
except ImportError:
    templated_email_available = False

def beta_confirm(email, **kwargs):
    """
    Send out email confirming that they requested an invite.
    """

    templates_folder = setting('BETA_EMAIL_TEMPLATES_DIR', 'hunger')
    templates_folder = os.path.join(templates_folder, '')
    from_email = kwargs.get('from_email', setting("DEFAULT_FROM_EMAIL"))
    if templates_folder == 'hunger':
        file_extension = 'email'
    else:
        file_extension = None

    context_dict = kwargs.copy()

    MandrillMail('beta_confirm.email', context=context_dict).send(
        from_email=from_email,
        recipient_list=[email],
    )

def beta_invite(email, code, request, **kwargs):
    """
    Email for sending out the invitation code to the user.
    Invitation URL is added to the context, so it can be rendered with standard
    django template engine.
    """
    context_dict = kwargs.copy()

    context_dict.setdefault(
        "invite_url",
        request.build_absolute_uri(reverse("beta_verify_invite", args=[code]))
    )
    context = Context(context_dict)

    from_email = kwargs.get('from_email', setting("DEFAULT_FROM_EMAIL"))
    html_content = text_content = None

    if kwargs.get('custom_message'):
        from hunger.utils import html2plain
        html_content = kwargs.get('custom_message').format(invite_url=context_dict['invite_url'])
        text_content = html2plain(html_content)

    MandrillMail('beta_invite.email', context=context_dict).send(
        from_email=from_email,
        recipient_list=[email],
        html=html_content,
        fulltext=text_content,
    )
