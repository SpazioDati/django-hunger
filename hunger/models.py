import string, random
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from .auth import User


def generate_invite_code():
    num_chars = getattr(settings, 'BETA_INVITE_CODE_LENGTH', 8)
    return ''.join(random.choice(string.letters) for i in xrange(num_chars))

class InvitationCode(models.Model):
    code = models.CharField(_(u"Invitation code"), blank=True, max_length=8, unique=True)
    is_used = models.BooleanField(_(u"Is Used"), default=False)
    is_invited = models.BooleanField(_('Is Invited'), default=False)

    email = models.EmailField(_('Email address'), unique=True)
    user = models.ForeignKey(User, blank=True, null=True, default=None)
    user_lang = models.CharField(blank=True, null=True, default='en-us', max_length=10)

    created = models.DateTimeField(_('Created'), auto_now_add=True)
    invited = models.DateTimeField(_(u"Invited"), blank=True, null=True)
    used = models.DateTimeField(_(u"Used"), blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_invite_code()

            if not kwargs.get("skip", False):
                from hunger.receivers import invitation_code_created
                from hunger.signals import invite_created
                invite_created.connect(invitation_code_created)
                invite_created.send(sender=self.__class__, email=self.email)

        try:
            del kwargs["skip"]
        except KeyError:
            pass

        super(InvitationCode, self).save(*args, **kwargs)


    @classmethod
    def validate_code(cls, code):
        #returns valid, exists
        try:
            invitation_code = InvitationCode.objects.get(code=code)
            if invitation_code.is_used:
                return False, True
            else:
                return True, True
        except InvitationCode.DoesNotExist:
            return False, False

