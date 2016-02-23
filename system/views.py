from django.shortcuts import render

def announcements(request):
    return render(request, 'system/announcements.html', {})
