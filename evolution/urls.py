from django.conf.urls import include, url
from django.contrib import admin

import system.urls
import contests.urls

urlpatterns = [
    url(r'^', include(system.urls)),
    url(r'^contest/', include(contests.urls)),
    url(r'^admin/', include(admin.site.urls)),
]
