import html
import markdown
import bleach
import reprlib
from datetime import timedelta

from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from allauth.account.models import EmailAddress
from allauth.utils import build_absolute_uri

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

    def __str__(self):
        return str(self.id) + ' (' + self.source_lang + ') ' + \
            reprlib.repr(self.source)


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
    'p',
    'table',
    'thead',
    'tr',
    'th',
    'td',
    'tbody',
    'tfoot',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6'
    # 'blockquote', # TODO support in css
    #  definition lists - TODO support them in css
    # 'dl',
    # 'dt',
    # 'dd'
]

ALLOWED_CSS_CLASSES = ['highlight', 'bp', 'c', 'c1', 'cm', 'cp', 'cs', 'err',
     'gd', 'ge', 'gh', 'gi', 'go', 'gp', 'gr', 'gs', 'gt', 'gu', 'hll', 'il',
      'k', 'kc', 'kd', 'kn', 'kp', 'kr', 'kt', 'm', 'mf', 'mh', 'mi', 'mo',
      'na', 'nb', 'nc', 'nd', 'ne', 'nf', 'ni', 'nl', 'nn', 'no', 'nt', 'nv',
      'o', 'ow', 's', 's1', 's2', 'sb', 'sc', 'sd', 'se', 'sh', 'si', 'sr',
      'ss', 'sx', 'vc', 'vg', 'vi', 'w']


def safe_class(name, value):
    return name == "class" and value in ALLOWED_CSS_CLASSES


MARKDOWN_ALLOWED_ATTRIBUTES = {
    'abbr': ['title'],
    'acronym': ['title'],
    'a': ['href', 'title'],
    'span': safe_class,
    'div': safe_class,
    'tr': ['align'],
    'th': ['align'],
    'td': ['align'],
    'tbody': ['align'],
    'tfoot': ['align']
}


def markdown_to_html(source):
    markdown_html = markdown.markdown(source, extensions=['mdx_partial_gfm'])
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

    def __str__(self):
        return str(self.id) + ': ' + reprlib.repr(self.title)


def validate_x(string):
    if string != 'x':
        raise ValidationError('%s is not \'x\'' % string)


def validate_email_not_used(email):
    existing_email = EmailAddress.objects.filter(email=email). \
        first()
    if existing_email:
        existing_user = existing_email.user
        raise ValidationError(
            "Email already associated with user: %s (%s)." %
            (existing_user.get_full_name(), existing_user.username))


class Invitation(models.Model):
    invited_email = models.EmailField(validators=[validate_email_not_used])
    invited_by = models.ForeignKey('auth.User', null=True)
    secret_code = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def is_expired(self):
        latest_acceptable = self.created_at + \
            timedelta(days=settings.INVITATION_EXPIRY)
        return timezone.now() > latest_acceptable

    def prepare(self):
        self.secret_code = User.objects.make_random_password(length=16)

    def send_email(self):
        site = Site.objects.get_current()
        subject = '[%s] Invitation' % site.name
        to = self.invited_email
        full_signup_url = build_absolute_uri(None, settings.SIGNUP_URL)
        # TODO, move to a template or something
        body_template = """\
Hello,

You have been invited to use {site_name}. We hope you'll like it.

Invited email: {invited_email}
Secret code: {secret_code}
Sign up url: {full_signup_url}

Enjoy,
{site_name} Team
"""
        body = body_template.format(
            site_name=site.name,
            invited_email=self.invited_email,
            secret_code=self.secret_code,
            full_signup_url=full_signup_url
        )
        email = EmailMessage(subject, body, to=[to])
        email.send()


class ClientInfo(models.Model):
    client_address = models.CharField(max_length=255)
    user_agent = models.TextField()
    referer = models.TextField()

    def extract_from(self, request):
        self.client_address = request.META.get('HTTP_X_FORWARDED_FOR',
            request.META.get('REMOTE_ADDR', 'unknown'))
        self.user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        self.referer = request.META.get('HTTP_REFERER', 'unknown')

    def __str__(self):
        return ' '.join([self.client_address, self.user_agent, self.referer])


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
