try:
    import importlib
except ImportError:
    from django.utils import importlib

from hunger.models import InvitationCode
from hunger.utils import setting, now

from .auth import User


def invitation_code_created(sender, email, **kwargs):
    """Send confirmation email to user."""
    email_module_name = setting('BETA_EMAIL_MODULE', 'hunger.email')
    email_module = importlib.import_module(email_module_name)
    email_function_name = setting('BETA_EMAIL_CONFIRM_FUNCTION', 'beta_confirm')
    email_function = getattr(email_module, email_function_name)
    email_function(email, **kwargs)


def invitation_code_sent(sender, email, invitation_code, **kwargs):
    """Send invitation code to user."""
    try:
        invitation_obj = InvitationCode.objects.get(email=email)
    except InvitationCode.DoesNotExist:
        try:
            User.objects.get(is_superuser=True, email=email)
        except User.DoesNotExist:
            return
    else:
        invitation_obj.is_invited = True
        invitation_obj.invited = now()
        invitation_obj.save()

    email_module_name = setting('BETA_EMAIL_MODULE', 'hunger.email')
    email_module = importlib.import_module(email_module_name)
    email_function_name = setting('BETA_EMAIL_INVITE_FUNCTION', 'beta_invite')
    email_function = getattr(email_module, email_function_name)
    email_function(email, invitation_code, **kwargs)


def invitation_code_used(sender, user, invitation_code, **kwargs):
    """Set the invitation code as used by user."""
    try:
        invitation_code = InvitationCode.objects.get(code=invitation_code)
    except InvitationCode.DoesNotExist:
        return

    invitation_code.user = user
    invitation_code.is_used = True
    invitation_code.used = now()
    invitation_code.save()
