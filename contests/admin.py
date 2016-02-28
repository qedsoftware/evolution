from django.contrib import admin

from contests.models import Contest

class ContestAdmin(admin.ModelAdmin):
    pass
admin.site.register(Contest, ContestAdmin)
