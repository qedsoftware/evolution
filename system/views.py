from django.shortcuts import render

from django.views.generic.list import ListView

from .models import NewsItem

from django_downloadview import StorageDownloadView


media_path = StorageDownloadView.as_view()

def title(text = None):
    return ' - '.join(filter(None, ["Evolution", text]))

class NewsList(ListView):
    context_object_name = 'news'
    template_name = "system/news.html"
    paginate_by = 10
    queryset = NewsItem.objects.select_related('content').all()

def user_settings(request):
    return render(request, 'system/user_settings.html', {})
