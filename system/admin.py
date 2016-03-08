from django.contrib import admin

from .models import Post, NewsItem, SystemSettings
from .forms import PostForm

class PostAdmin(admin.ModelAdmin):
    form = PostForm

admin.site.register(Post, PostAdmin)

class NewsItemAdmin(admin.ModelAdmin):
    pass

admin.site.register(NewsItem, NewsItemAdmin)

class SystemSettingsAdmin(admin.ModelAdmin):
    exclude = ['force_one']

admin.site.register(SystemSettings, SystemSettingsAdmin)
