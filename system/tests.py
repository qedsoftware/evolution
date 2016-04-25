from django.test import TestCase, Client
from django.db.utils import IntegrityError
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from django_webtest import WebTest

from .models import PostData, Post, SystemSettings
from .utils import calculate_once


def new_user(username, admin=False):
    user = User.objects.create_user(username, username + '@example.com',
            'password')
    user.first_name = username
    user.last_name = username + 'son'
    if admin:
        user.is_superuser = True
        user.is_staff = True
    user.save()
    return user


class SimpleSanityCheck(TestCase):
    def test(self):
        client = Client()
        client.get('/')


class PostDataTest(TestCase):
    def test_init(self):
        pd = PostData(source='a', source_lang='b', html='c')
        self.assertEqual(pd.source, 'a')
        self.assertEqual(pd.source_lang, 'b')
        self.assertEqual(pd.html, 'c')

    def test_from_source(self):
        pd = PostData.from_source('a', 'b')
        self.assertEqual(pd.source, 'a')
        self.assertEqual(pd.source_lang, 'b')
        self.assertIsNone(pd.html)

    def test_build_plain(self):
        plain = PostData.from_source('ala ma kota<script>', 'plaintext')
        plain.build_html()
        self.assertEqual('ala ma kota&lt;script&gt;', plain.html)

    def test_build_html(self):
        html = PostData.from_source('ala ma kota<script>', 'html')
        html.build_html()
        self.assertEqual('ala ma kota<script>', html.html)

    def test_build_markdown(self):
        markdown = PostData.from_source('**test**', 'markdown')
        markdown.build_html()
        self.assertEqual('<p><strong>test</strong></p>', markdown.html)
        markdown_security = PostData.from_source('<script>', 'markdown')
        markdown_security.build_html()
        self.assertFalse('<script>' in markdown_security.html)

    def test_markdown_highlighting(self):
        source = """\
```python
class HighlightingTest(object):
    pass

for i in [1, 2, 3]:
    print(17)
```
"""
        markdown = PostData.from_source(source, 'markdown')
        markdown.build_html()
        # no tag should be escaped
        self.assertFalse('&lt' in markdown.html)
        self.assertFalse('&gt' in markdown.html)
        self.assertTrue('<div class="highlight">' in markdown.html)
        self.assertTrue('<span class="k">' in markdown.html)

    def test_markdown_table(self):
        source = """\
| Tables        | Are           | Cool  |
| ------------- |:-------------:| -----:|
| col 3 is      | right-aligned | $1600 |
| col 2 is      | centered      |   $12 |
| zebra stripes | are neat      |    $1 |
"""
        markdown = PostData.from_source(source, 'markdown')
        markdown.build_html()
        self.assertFalse('&lt' in markdown.html)
        self.assertFalse('&gt' in markdown.html)


class PostTest(TestCase):
    def test_from_data(self):
        post = Post()
        pd = PostData(source='a', source_lang='b', html='c')
        post.from_data(pd)
        self.assertEqual(post.source, 'a')
        self.assertEqual(post.source_lang, 'b')
        self.assertEqual(post.html, 'c')

    def test_to_data(self):
        post = Post(source='a', source_lang='b', html='c')
        pd = post.to_data()
        self.assertEqual(pd.source, 'a')
        self.assertEqual(pd.source_lang, 'b')
        self.assertEqual(pd.html, 'c')


class SystemSettingsTest(TestCase):
    def setUp(self):
        global_msg = PostData.from_source('__global_message__', 'html')
        global_msg.build_html()
        footer = PostData.from_source('__footer__', 'html')
        footer.build_html()
        settings = SystemSettings.get()
        settings.global_message = Post.new_from_data(global_msg)
        settings.footer = Post.new_from_data(footer)
        settings.save()

    def test_view(self):
        client = Client()
        response = client.get('/')
        self.assertContains(response, '__global_message__')
        self.assertContains(response, '__footer__')


class AdditionalSettingsTest(TestCase):
    def test_simple(self):
        orig_settings = SystemSettings.get()
        settings = SystemSettings()
        self.assertRaises(IntegrityError, settings.save)

    def test_changed_force_one(self):
        settings = SystemSettings()
        settings.force_one = 'y'
        settings.save()


class CalculateOnceTest(TestCase):

    foo_call_count = 0

    @calculate_once
    def foo(self):
        self.foo_call_count = self.foo_call_count + 1
        return list(range(5))

    def test(self):
        self.assertEqual(self.foo_call_count, 0)
        self.assertEqual(self.foo, [0, 1, 2, 3, 4])
        self.assertEqual(self.foo_call_count, 1)
        self.assertEqual(self.foo, [0, 1, 2, 3, 4])
        self.assertEqual(self.foo_call_count, 1)
        self.assertEqual(self.foo, [0, 1, 2, 3, 4])
        self.assertEqual(self.foo_call_count, 1)


class EmptySignupTest(WebTest):
    def test(self):
        page = self.app.get('/accounts/signup/')
        form = page.forms['signup_form']
        form.submit()


class MessagesTestViewTest(WebTest):
    def test(self):
        page = self.app.get('/test_view/messages')
        page.mustcontain('Success', 'Warning', 'Error')


class StaticMessagesTestViewTest(WebTest):
    csrf_checks = False

    def test(self):
        page = self.app.post('/test_view/static_messages').follow()
        page.mustcontain('get1', 'get2', no=['other1', 'other2'])


class SuperuserManualTest(WebTest):
    def test(self):
        admin = new_user('admin', admin=True)
        page = self.app.get(reverse('superuser_manual'), user=admin)


class UserSettingsTest(WebTest):
    def test_anonymous(self):
        page = self.app.get(reverse('user_settings')).follow()
        page.mustcontain('Please log in')

    def test(self):
        user = new_user('test')
        page = self.app.get(reverse('user_settings'), user=user)
        page.mustcontain('Change password')
        page.mustcontain('Manage email address')
