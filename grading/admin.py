from django.contrib import admin

from .models import ScoringScript, DataGrader, Submission, GradingAttempt


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'current_attempt', 'needs_grading',
    'needs_grading_at', 'score', 'scoring_status']
    list_filter = ['needs_grading', 'scoring_status']


@admin.register(ScoringScript)
class ScoringScriptAdmin(admin.ModelAdmin):
    pass


@admin.register(DataGrader)
class DataGraderAdmin(admin.ModelAdmin):
    list_display = ['id', 'scoring_script', 'time_limit_ms',
        'memory_limit_bytes']
    search_fields = ['scoring_script__id']


@admin.register(GradingAttempt)
class GradingAttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'finished_at', 'scoring_status',
        'started', 'finished', 'succeeded', 'aborted']
    list_filter = ['scoring_status', 'started', 'finished', 'succeeded',
        'aborted']
