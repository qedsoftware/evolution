from django.conf.urls import include, url
from django.contrib import admin

import system.urls

urlpatterns = [
    url(r'^', include(system.urls)),
    url(r'^admin/', include(admin.site.urls)),
]
