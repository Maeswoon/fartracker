from django.contrib import admin

from .models import Team, LaunchRail, Bunker, SiteStatus

# Register your models here.
admin.site.register(Team)
admin.site.register(LaunchRail)
admin.site.register(Bunker)
admin.site.register(SiteStatus)

