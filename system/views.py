from django.shortcuts import render

def title(text = None):
    return ' - '.join(filter(None, ["Evolution", text]))

def announcements(request):
    return render(request, 'system/announcements.html', {})

def user_settings(request):
    return render(request, 'system/user_settings.html', {})
