from django.test import TestCase, Client

from .models import PostData, Post, SystemSettings

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
