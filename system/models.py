import html
import markdown
import gfm

from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    source_lang = models.CharField(max_length=20)
    source = models.TextField()
    html = models.TextField()

    def to_data(self):
        return PostData(
            source_lang=self.source_lang,
            source = self.source,
            html = self.html
        )

    def from_data(self, data):
        self.source_lang = data.source_lang
        self.source = data.source
        self.html = data.html

    @classmethod
    def new_from_data(cls, data):
        post = cls()
        post.from_data(data)
        post.save()
        return post

def markdown_to_html(source):
    return markdown.markdown(source, extensions=['mdx_gfm'])

post_source_processors = {
    'html': lambda source: source,  # identity
    'plaintext': html.escape,
    'markdown': markdown_to_html
}

class PostData(object):
    source_lang = None
    source = None
    html = None

    @classmethod
    def from_source(cls, source, source_lang):
        data = cls()
        data.source = source
        data.source_lang = source_lang
        return data

    def build_html(self):
        self.html = post_source_processors[self.source_lang](self.source)

class NewsItem(models.Model):
    author = models.ForeignKey('auth.User')
    created = models.DateTimeField()
    content = models.OneToOneField('Post')

class SystemSettings(models.Model):
    global_message = models.ForeignKey('Post', related_name='+', null=True)
    footer = models.ForeignKey('Post', related_name='+')
