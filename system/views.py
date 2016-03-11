from django.shortcuts import render

from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django_downloadview import StorageDownloadView

from django.utils.safestring import mark_safe
from django.contrib import messages

from .models import NewsItem


class AdminDownload(UserPassesTestMixin, StorageDownloadView):

    def test_func(self):
        return self.request.user.is_superuser

def title(text = None):
    return ' - '.join(filter(None, ["Evolution", text]))

class NewsList(ListView):
    context_object_name = 'news'
    template_name = "system/news.html"
    paginate_by = 10
    queryset = NewsItem.objects.select_related('content').all()

def user_settings(request):
    return render(request, 'system/user_settings.html', {})

def messages_test_view(request):
    messages.set_level(request, messages.DEBUG)
    messages.add_message(request, messages.SUCCESS,
        mark_safe('Success. You are no longer observing contest '
            '<strong>Data Science Cup</strong>.'))
    messages.add_message(request, messages.SUCCESS,
        mark_safe('<p>Success</p><p>You have changed the contests. Lorem ipsum dolor sit'
            'amet augue at tortor. Praesent et magnis dis parturient montes,'
            'nascetur rig di amet.</p>'
            '<p>Lorem ipsum Fugiat culpa mollit Duis enim dolor proident et'
            'elit adipisicing velit est pariatur dolor cupidatat Duis'
            'incididunt consequat Ut ullamco commodo aliquip esse officia'
            ' cupidatat in aute irure dolor consequat minim.</p>'))
    messages.add_message(request, messages.DEBUG,
        mark_safe('This is a debug message. <pre>blebleble</pre>'))
    messages.add_message(request, messages.INFO,
        mark_safe('This is an info message. The weather is nice today.'))
    messages.add_message(request, messages.WARNING,
        mark_safe("Warning: It's a trap!"))
    messages.add_message(request, messages.ERROR,
        mark_safe("Error. Something blew up badly."))
    return render(request, 'system/title_and_text.html', {
        'title': title('Message Test'),
        'content_title': 'Message Test',
        'text': "Nothing to do here"
    })
