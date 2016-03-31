from django.contrib import admin

from contests.models import Contest, Team, TeamMember, ContestStage, \
    ContestSubmission, ContestSubmissionEvent


class ContestAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'bigger_better', 'description']
    search_fields = ['name', 'code']
    list_filter = ['bigger_better']
    list_display_links = ['id', 'name', 'code']


admin.site.register(Contest, ContestAdmin)


class ContestStageAdmin(admin.ModelAdmin):
    list_display = ['id', 'contest', 'begin', 'end', 'published_results',
        'requires_selection', 'selected_limit']
    search_fields = ['contest__name', 'contest__code']
    list_filter = ['published_results', 'requires_selection', 'selected_limit']

admin.site.register(ContestStage, ContestStageAdmin)


class ContestSubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'stage', 'contest', 'team', 'selected']
    search_fields = ['team__name']
    list_filter = ['selected']

admin.site.register(ContestSubmission, ContestSubmissionAdmin)


class TeamAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'contest']
    search_fields = ['name']
    list_filter = ['contest']
    list_display_links = ['id', 'name']


admin.site.register(Team, TeamAdmin)


class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['id', 'team', 'user', 'contest']
    search_fields = ['user__username', 'user__first_name', 'user__last_name',
        'team__name']
    list_filter = ['contest']


admin.site.register(TeamMember, TeamMemberAdmin)


class ContestSubmissionEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'submission', 'client_info']
    search_fields = ['client_info__client_address', 'client_info__user_agent',
        'client_info__referer']


admin.site.register(ContestSubmissionEvent, ContestSubmissionEventAdmin)
