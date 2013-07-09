import re
import bleach
import datetime

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def setting(name, default=None):
    """Return setting value for given name or default value."""
    return getattr(settings, name, default)


def now():
    """Backwards compatible now function when USE_TZ=False."""
    if setting('USE_TZ'):
        from django.utils import timezone
        return timezone.now()
    else:
        return datetime.datetime.now()


def html2plain(html):
    """ try to convert html code to plain text for being used in email body
    """
    return bleach.clean(
        tags=[],
        strip=True,
        text=re.sub(
            '(</p>|</div>)', '\\1\n\n',
            re.sub(
                '(<br ?/?>)', '\n',
                re.sub('(\n|\r)', '', html)
            )
        )
    )


class MandrillMail(object):
    def __init__(self, template_name, context):
        from xml.etree import cElementTree as ET

        xml_body = render_to_string('hunger/' + template_name, context)
        root = ET.fromstring(xml_body)
        self.blocks = {}

        for child in root:
            if child.text:
                self.blocks[child.tag] = child.text.strip()

    def send(self, from_email, recipient_list, **kwargs):
        blocks = dict(self.blocks, **{k:v for k, v in kwargs.items() if v})
        
        title = blocks.get('title')
        cta_link = blocks.get('cta_link')
        cta_label = blocks.get('cta_label')

        msg = EmailMessage(
            subject=blocks.get('subject'),
            from_email=from_email,
            to=recipient_list
        )
        msg.template_name = setting('BETA_MANDRILL_TEMPLATE')
        msg.template_content = {
            "title": title,
            "body_content": blocks.get('html'),
            "button_content": '',  # default
        }

        msg.global_merge_vars = {
            'FULLTEXTTITLE': title,
            'FULLTEXTCONTENT': blocks.get('fulltext'),
            'FULLTEXTCTA': '',  # default
        }

        if cta_label and cta_link:
            msg.global_merge_vars['FULLTEXTCTA'] = '{}: {}'.format(
                cta_link,
                cta_label
            )
            msg.template_content['button_content'] = \
                '<a href="{}" target="_blank">{}</a>'.format(
                    cta_link, cta_label
                )

        msg.send()
