from django.contrib import admin

from .models import Post, NewsItem

class PostAdmin(admin.ModelAdmin):
    pass

admin.site.register(Post, PostAdmin)

class NewsItemAdmin(admin.ModelAdmin):
    pass

admin.site.register(NewsItem, NewsItemAdmin)
