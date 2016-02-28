from django.shortcuts import render

def title(text = None):
    return ' - '.join(filter(None, ["Evolution", text]))

def announcements(request):
    return render(request, 'system/announcements.html', {
        'next': "http://google.com"
    })
''
