from django.conf.urls import include, url
from django.contrib import admin

from . import views

import contests.urls

urlpatterns = [
    url(r'^$', views.NewsList.as_view(), name="news"),
    url(r'^user-settings/$', views.user_settings, name='user_settings'),
    url(r'^', include(contests.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^media/(?P<path>[a-zA-Z0-9_.-]+)$',
        views.AdminDownload.as_view(), name='media_path'),
    url(r'^invite/$', views.InviteView.as_view(), name="invite"),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^superuser_manual/$', views.SuperuserManual.as_view(),
        name='superuser_manual'),
    # below are the patterns made for front-end testing, they should not
    # be linked anywhere or change any data
    url(r'^test_view/messages$', views.messages_test_view),
    url(r'^test_view/static_messages$', views.static_messages_test_view),
]
