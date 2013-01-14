import csv
from datetime import datetime
from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from hunger.models import InvitationCode
from hunger.signals import invite_sent
from hunger.receivers import invitation_code_sent


invite_sent.connect(invitation_code_sent)


class InvitationCodeAdmin(admin.ModelAdmin):
    """Admin for invitation code"""
    list_display = ('code', 'is_used', 'is_invited', 'email', 'user', 'user_lang', 'created', 'invited', 'used', )
    list_filter = ('is_used', 'is_invited', 'created', 'invited', 'used', 'user_lang')
    search_fields = ['email']
    actions = ['send_invite', 'resend_invite', 'personalize_invite', 'export_email']

    def get_urls(self):
        from django.conf.urls import patterns, url

        urlpatterns = super(InvitationCodeAdmin, self).get_urls()
        extra_urls = patterns('',
            url(r'^confirm-invite/$', self.confirm_invite,
             name='hunger_invitationcode_confirminvite'),
            url(r'^send-invitation-code/$', self.send_invitation_code,
             name='hunger_invitationcode_sendinvite'),
        )
        return extra_urls + urlpatterns

    def confirm_invite(self, request):
        ids = request.GET.get('ids', '').split(',')

        if request.method == 'POST':
            queryset = InvitationCode.objects.filter(pk__in=ids)
            self._send_invitation_email(
                request, queryset, request.GET.get('action'),
            )
            return HttpResponseRedirect(
                reverse('admin:hunger_invitationcode_changelist')
            )

        context = {
            'app_label': self.opts.app_label,
            'has_change_permission': self.has_change_permission(request),
            'current_app': self.admin_site.name,
            'opts': self.model._meta,
            'action': request.GET.get('action'),
            'object_list': InvitationCode.objects.filter(pk__in=ids)
        }
        return render(request,
            'admin/hunger/invitationcode/confirm_invite.html',
            context
        )

    def send_invitation_code(self, request):
        from django.shortcuts import render
        from hunger.forms import InvitationEmailForm
        from django.utils.safestring import mark_safe

        if request.method == "POST":
            form = InvitationEmailForm(data=request.POST)
            if form.is_valid():
                ids = form.cleaned_data['ids'].split(',')
                queryset = InvitationCode.objects.filter(pk__in=ids)
                self._send_invitation_email(
                    request, queryset, form.cleaned_data['action'],
                    custom_message=mark_safe(form.cleaned_data['message']),
                )
                return HttpResponseRedirect(
                    reverse('admin:hunger_invitationcode_changelist')
                )
        else:
            form = InvitationEmailForm(initial=request.GET)

        context = {
            'app_label': self.opts.app_label,
            'has_change_permission': self.has_change_permission(request),
            'current_app': self.admin_site.name,
            'opts': self.model._meta,
            'form': form,
        }
        return render(request,
            'admin/hunger/invitationcode/send_invitation_code.html',
            context
        )

    def export_email(self, request, queryset):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=email.csv'
        writer = csv.writer(response)

        writer.writerow(["email", "is_used", "is_invited", "created", "invited", "used"])

        for obj in queryset:
            code = obj
            email = code.email
            is_used = code.is_used
            is_invited = code.is_invited
            created = datetime.strftime(code.created, "%Y-%m-%d %H:%M:%S")
            try:
                invited = datetime.strftime(code.invited, "%Y-%m-%d %H:%M:%S")
            except TypeError:
                invited = ""
            try:
                used = datetime.strftime(code.used, "%Y-%m-%d %H:%M:%S")
            except TypeError:
                used = ""

            if len(email) >0 and email != "None":
                row = [email, is_used, is_invited, created, invited, used]
                row.append(email)
                writer.writerow(row)
            # Return CSV file to browser as download
        return response

    def send_invite(self, request, queryset, action='send'):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(
            '{0}?ids={1}&action={2}'.format(
                reverse('admin:hunger_invitationcode_confirminvite'),
                ','.join(selected), action
            )
        )

    def resend_invite(self, request, queryset):
        return self.send_invite(request, queryset, action='resend')

    def personalize_invite(self, request, queryset):
        if queryset.count() != 1:
            messages.error(request, "You can personalize only one invitation at a time.")
            return
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(
            '{0}?ids={1}'.format(
                reverse('admin:hunger_invitationcode_sendinvite'),
                ','.join(selected)
            )
        )

    def _send_invitation_email(self, request, queryset, action, custom_message=''):
        from django.utils import translation

        n_sent = 0
        for obj in queryset:
            if (action == 'send' and not obj.is_invited) \
                    or (action == 'resend' and obj.is_invited):
                cur_language = translation.get_language()
                try:
                    translation.activate(obj.user_lang)
                    invite_sent.send(sender=self.__class__, email=obj.email,
                        invitation_code=obj.code,
                        user=obj.user, request=request,
                        custom_message=custom_message)
                    n_sent += 1
                finally:
                    translation.activate(cur_language)

        messages.info(request,
            _('{0} invitation email(s) sent correctly.').format(n_sent)
        )


admin.site.register(InvitationCode, InvitationCodeAdmin)
