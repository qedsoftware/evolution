from django.shortcuts import render
from django.views.generic import View, FormView
from django.views.generic.base import ContextMixin
from django.views.generic.list import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured
from django_downloadview import StorageDownloadView
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse

from django.utils.safestring import mark_safe
from django.contrib import messages
from django.contrib.messages.storage.base import Message

from .forms import InviteForm

from .models import NewsItem, PostData


# Sometimes it is useful to show some messages only for
# the original request. Permanent messages are example of that.
# Especially, when they are specific to some part of the system
def add_static_message(context, level, msg, extra_tags=""):
    msg = Message(level, msg, extra_tags)
    if 'static_messages' in context:
        context['static_messages'].append(msg)
    else:
        context['static_messages'] = [msg]


class AdminDownload(UserPassesTestMixin, StorageDownloadView):

    def test_func(self):
        return self.request.user.is_superuser


def title(text=None):
    return ' - '.join(filter(None, ["Evolution", text]))


class NewsList(ListView):
    context_object_name = 'news'
    template_name = "system/news.html"
    paginate_by = 10
    queryset = NewsItem.objects.select_related('content').all()


def user_settings(request):
    return render(request, 'system/user_settings.html', {})


class PostDataView(ContextMixin, View):
    """
    Generic View that allows "static posts".

    It renders the template in the specified language then builds html using
    the same mechanism as Posts. Result is added to the context as `text`.
    Then it renders external template, with the resulting context.

    Currently it goes through building html on every request, if this becomes
    a performance issue, we may want to cache that.
    """

    post_template_name = None
    source_lang = None
    external_template_name = "system/title_and_text.html"

    def get(self, request, *args, **kwargs):
        if not self.post_template_name:
            raise ImproperlyConfigured(
                "You need to specify post_template_name")
        if not self.source_lang:
            raise ImproperlyConfigured("You need to specify source_lang")

        context = self.get_context_data(**kwargs)
        source = render_to_string(self.post_template_name, context=context,
            request=request)
        post = PostData.from_source(source, self.source_lang)
        post.build_html()
        context['text'] = post.html
        return render(request, self.external_template_name, context)


class InviteView(UserPassesTestMixin, FormView):
    form_class = InviteForm
    template_name = "system/invite.html"

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        form.instance.invited_by = self.request.user
        form.instance.prepare()
        invitation = form.save()
        invitation.send_email()
        messages.add_message(self.request, messages.SUCCESS,
            mark_safe("Invitation sent to <strong>%s</strong>" %
                invitation.invited_email))
        return super(InviteView, self).form_valid(form)

    def get_success_url(self):
        return reverse('invite')


def messages_test_view(request):
    messages.set_level(request, messages.DEBUG)
    messages.add_message(request, messages.SUCCESS,
        mark_safe('Success. You are no longer observing contest '
            '<strong>Data Science Cup</strong>.'))
    messages.add_message(request, messages.SUCCESS,
        mark_safe('<p>Success</p><p>You have changed the contests. '
            'Lorem ipsum dolor sit'
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


class SuperuserManual(UserPassesTestMixin, PostDataView):
    post_template_name = "contests/superuser_manual.md"
    source_lang = 'markdown'
    content_title = "Superuser Manual"

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super(SuperuserManual, self).get_context_data(**kwargs)
        context['content_title'] = self.content_title
        return context
