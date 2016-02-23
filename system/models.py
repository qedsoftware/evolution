from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    source_lang = models.CharField(max_length=20)
    source = models.TextField()
    html = models.TextField()

class Announcement(models.Model):
    author = models.ForeignKey('auth.User')
    created = models.DateTimeField()
    content = models.ForeignKey('Post', related_name='+')

class SystemSettings(models.Model):
    global_message = models.ForeignKey('Post', related_name='+', null=True)
    footer = models.ForeignKey('Post', related_name='+')
