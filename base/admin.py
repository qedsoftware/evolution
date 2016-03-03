from django.contrib import admin

from .models import ScoringScript, DataGrader, Submission, GradingAttempt

class SubmissionAdmin(admin.ModelAdmin):
    pass
admin.site.register(Submission, SubmissionAdmin)

class ScoringScriptAdmin(admin.ModelAdmin):
    pass
admin.site.register(ScoringScript, ScoringScriptAdmin)

class DataGraderAdmin(admin.ModelAdmin):
    pass
admin.site.register(DataGrader, DataGraderAdmin)

class GradingAttemptAdmin(admin.ModelAdmin):
    pass
admin.site.register(GradingAttempt, GradingAttemptAdmin)
