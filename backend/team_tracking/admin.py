from django import forms
from django.contrib import admin

from .models import Team, LaunchRail, Bunker, SiteStatus, SalvoSchedule, ScheduleChangeLog, Vote, VoteBallot

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


@admin.register(ScheduleChangeLog)
class ScheduleChangeLogAdmin(admin.ModelAdmin):
    list_display = ['team_identifier', 'timestamp']
    readonly_fields = ['timestamp', 'team_identifier', 'data']
    list_filter = ['team_identifier']
    ordering = ['-timestamp']


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at', 'expires_at', 'is_active']
    readonly_fields = ['created_at', 'created_by', 'eligible_voters']
    list_filter = ['is_active']
    ordering = ['-created_at']


@admin.register(VoteBallot)
class VoteBallotAdmin(admin.ModelAdmin):
    list_display = ['vote', 'user', 'choice', 'cast_at']
    readonly_fields = ['cast_at']
    list_filter = ['vote']
    ordering = ['-cast_at']

