from django.contrib import admin

from contests.models import Contest, Team, TeamMember, ContestStage

class ContestAdmin(admin.ModelAdmin):
    pass
admin.site.register(Contest, ContestAdmin)

class ContestStageAdmin(admin.ModelAdmin):
    pass
admin.site.register(ContestStage, ContestStageAdmin)

class TeamAdmin(admin.ModelAdmin):
    pass
admin.site.register(Team, TeamAdmin)

class TeamMemberAdmin(admin.ModelAdmin):
    pass
admin.site.register(TeamMember, TeamMemberAdmin)



