from django.contrib import admin

from .models import Post, NewsItem, Invitation, SystemSettings
from .forms import PostForm


class PostAdmin(admin.ModelAdmin):
    form = PostForm
    list_display = ['id', 'source_lang', 'source']
    search_fields = ['source']


admin.site.register(Post, PostAdmin)


class NewsItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'created', 'title', 'content']
    search_fields = ['title', 'content__source']


admin.site.register(NewsItem, NewsItemAdmin)


class InvitationAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'invited_email', 'accepted',
                    'is_expired']
    search_fields = ['invited_email']
    list_filter = ['accepted']


admin.site.register(Invitation, InvitationAdmin)


class SystemSettingsAdmin(admin.ModelAdmin):
    exclude = ['force_one']
    list_display = ('global_message', 'footer')


admin.site.register(SystemSettings, SystemSettingsAdmin)
