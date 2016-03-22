from django.contrib import admin

from .models import ScoringScript, DataGrader, Submission, GradingAttempt


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'current_attempt', 'needs_grading',
    'needs_grading_at', 'score', 'scoring_status']
    list_filter = ['needs_grading', 'scoring_status']

admin.site.register(Submission, SubmissionAdmin)


class ScoringScriptAdmin(admin.ModelAdmin):
    pass

admin.site.register(ScoringScript, ScoringScriptAdmin)


class DataGraderAdmin(admin.ModelAdmin):
    list_display = ['id', 'scoring_script', 'time_limit_ms',
        'memory_limit_bytes']
    search_fields = ['scoring_script__id']
admin.site.register(DataGrader, DataGraderAdmin)


class GradingAttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'finished_at', 'scoring_status',
        'started', 'finished', 'succed', 'aborted']
    list_filter = ['scoring_status', 'started', 'finished', 'succed',
        'aborted']

admin.site.register(GradingAttempt, GradingAttemptAdmin)
