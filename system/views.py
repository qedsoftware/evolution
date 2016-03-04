from django.shortcuts import render

def title(text = None):
    return ' - '.join(filter(None, ["Evolution", text]))

def news(request):
    return render(request, 'system/news.html', {})

def user_settings(request):
    return render(request, 'system/user_settings.html', {})
