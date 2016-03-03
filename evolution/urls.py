from django.conf.urls import include, url

import system.urls

urlpatterns = [
    url(r'^', include(system.urls)),
]
