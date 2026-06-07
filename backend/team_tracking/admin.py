from django import forms
from django.contrib import admin

from .models import Team, LaunchRail, Bunker, SiteStatus, SalvoSchedule

# Register your models here.
admin.site.register(Team)
admin.site.register(LaunchRail)
admin.site.register(Bunker)
admin.site.register(SiteStatus)


@admin.register(SalvoSchedule)
class SalvoScheduleAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'updated_at']
    readonly_fields = ['updated_at']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        json_attrs = {'rows': 15, 'style': 'font-family: monospace; width: 600px;'}
        form.base_fields['lane_definitions'].widget = forms.Textarea(attrs=json_attrs)
        form.base_fields['lane_teams'].widget = forms.Textarea(attrs={'rows': 20, 'style': 'font-family: monospace; width: 600px;'})
        return form

