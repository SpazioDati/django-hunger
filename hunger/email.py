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
    return

    if templated_email_available:
        send_templated_mail(
            template_name='beta_confirm',
            from_email=from_email,
            recipient_list=[email],
            context=context_dict,
            template_dir=templates_folder,
            file_extension=file_extension,
        )
    else:
        plaintext = get_template(os.path.join(templates_folder, 'beta_confirm.txt'))
        html = get_template(os.path.join(templates_folder, 'beta_confirm.html'))
        subject = render_to_string(os.path.join(templates_folder, 'beta_confirm_subject.txt'), context_dict)

        headers = {}
        if setting('BETA_EMAIL_SET_FROM_HEADER', True):
            headers['From'] = '%s' % from_email

        text_content = plaintext.render(Context())
        html_content = html.render(Context())
        msg = EmailMultiAlternatives(subject, text_content, from_email, [email], headers=headers)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

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

    templates_folder = setting('BETA_EMAIL_TEMPLATES_DIR', 'hunger')
    templates_folder = os.path.join(templates_folder, '')
    from_email = kwargs.get('from_email', setting("DEFAULT_FROM_EMAIL"))
    if templates_folder == 'hunger':
        file_extension = 'email'
    else:
        file_extension = None

    if templated_email_available:
        send_templated_mail(
            template_name='beta_invite',
            from_email=from_email,
            recipient_list=[email],
            context=context_dict,
            template_dir=templates_folder,
            file_extension=file_extension,
        )
    else:
        if not kwargs.get('custom_message'):
            plaintext = get_template(os.path.join(templates_folder, 'beta_invite.txt'))
            html = get_template(os.path.join(templates_folder, 'beta_invite.html'))
            text_content = plaintext.render(context)
            html_content = html.render(context)
        else:
            from hunger.utils import html2plain
            html_content = kwargs.get('custom_message').format(invite_url=context_dict['invite_url'])
            text_content = html2plain(html_content)

        headers = {}
        if setting('BETA_EMAIL_SET_FROM_HEADER', True):
            headers['From'] = '%s' % from_email

        subject = render_to_string(os.path.join(templates_folder, 'beta_invite_subject.txt'), context)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [email], headers=headers)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
