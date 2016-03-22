from django.conf import settings

from .models import SystemSettings


def system_settings(request):
    system_settings = SystemSettings.get()
    return {'system_settings': system_settings}


def logo_link(request):
    return {'logo_link': settings.LOGO_LINK_URL}
