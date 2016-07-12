from django.contrib import admin

from .models import Post, NewsItem, Invitation, ClientInfo, SystemSettings
from .forms import PostForm


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostForm
    list_display = ['id', 'source_lang', 'source']
    search_fields = ['source']


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'created', 'title', 'content']
    search_fields = ['title', 'content__source']


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'invited_email', 'accepted',
                    'is_expired']
    search_fields = ['invited_email']
    list_filter = ['accepted']


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    exclude = ['force_one']


@admin.register(ClientInfo)
class ClientInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_address', 'user_agent', 'referer')
