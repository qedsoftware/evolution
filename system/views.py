from django.shortcuts import render

from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django_downloadview import StorageDownloadView

from .models import NewsItem


class AdminDownload(UserPassesTestMixin, StorageDownloadView):

    def test_func(self):
        return self.request.user.is_superuser


media_path = AdminDownload.as_view()

def title(text = None):
    return ' - '.join(filter(None, ["Evolution", text]))

class NewsList(ListView):
    context_object_name = 'news'
    template_name = "system/news.html"
    paginate_by = 10
    queryset = NewsItem.objects.select_related('content').all()

def user_settings(request):
    return render(request, 'system/user_settings.html', {})
