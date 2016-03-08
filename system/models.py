import html
import markdown
import gfm
import bleach

from django.db import models, transaction
from django.contrib.auth.models import User

SOURCE_LANGUAGES = (
    ('html', 'HTML'),
    ('plaintext', 'Plain Text'),
    ('markdown', 'Github-flavored Markdown')
)

class Post(models.Model):
    source_lang = models.CharField(max_length=20, default='markdown',
        choices=SOURCE_LANGUAGES)
    source = models.TextField()
    html = models.TextField()

    def to_data(self):
        return PostData(
            source_lang=self.source_lang,
            source=self.source,
            html=self.html
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

MARKDOWN_ALLOWED_TAGS = [
    'a',
    'abbr',
    'acronym',
    'b',
    'br',
    'blockquote',
    'code',
    'div',
    'em',
    'i',
    'li',
    'ol',
    'pre',
    'span',
    'strong',
    'ul',
    'p'
]

ALLOWED_CSS_CLASSES = ['highlight', 'bp', 'c', 'c1', 'cm', 'cp', 'cs', 'err', 'gd', 'ge', 'gh', 'gi', 'go', 'gp', 'gr', 'gs', 'gt', 'gu', 'hll', 'il', 'k', 'kc', 'kd', 'kn', 'kp', 'kr', 'kt', 'm', 'mf', 'mh', 'mi', 'mo', 'na', 'nb', 'nc', 'nd', 'ne', 'nf', 'ni', 'nl', 'nn', 'no', 'nt', 'nv', 'o', 'ow', 's', 's1', 's2', 'sb', 'sc', 'sd', 'se', 'sh', 'si', 'sr', 'ss', 'sx', 'vc', 'vg', 'vi', 'w']

def safe_class(name, value):
    return name == "class" and value in ALLOWED_CSS_CLASSES

MARKDOWN_ALLOWED_ATTRIBUTES = {
    'abbr': ['title'],
    'acronym': ['title'],
    'a': ['href', 'title'],
    'span': safe_class,
    'div': safe_class
}

def markdown_to_html(source):
    markdown_html = markdown.markdown(source, extensions=['mdx_gfm'])
    return bleach.clean(markdown_html,
        tags=MARKDOWN_ALLOWED_TAGS,
        attributes=MARKDOWN_ALLOWED_ATTRIBUTES)

post_source_processors = {
    'html': lambda source: source,  # identity
    'plaintext': html.escape,
    'markdown': markdown_to_html
}

class PostData(object):
    source_lang = None
    source = None
    html = None

    def __init__(self, source=None, source_lang=None, html=None):
        self.source = source
        self.source_lang = source_lang
        self.html = html

    @classmethod
    def from_source(cls, source, source_lang):
        data = cls()
        data.source = source
        data.source_lang = source_lang
        return data

    def build_html(self):
        self.html = post_source_processors[self.source_lang](self.source)

class NewsItem(models.Model):
    created = models.DateTimeField()
    title = models.CharField(max_length=200)
    content = models.OneToOneField('Post')

def validate_x(string):
    if string != 'x':
        raise ValidationError('%s is not \'x\'' % string)

class SystemSettings(models.Model):
    class Meta:
        verbose_name = "System settings"
        verbose_name_plural = "System settings"
    # hack to ensure there is only one settings row
    force_one = models.CharField(max_length=1, default='x', unique=True,
        validators=[validate_x])
    global_message = models.ForeignKey('Post', related_name='+', null=True)
    footer = models.ForeignKey('Post', related_name='+', null=True)

    @classmethod
    @transaction.atomic
    def get(cls):
        return cls.objects.get_or_create()[0]
