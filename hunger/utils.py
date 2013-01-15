import re
import bleach
import datetime
from django.conf import settings


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
