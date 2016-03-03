from django.conf.urls import include, url
from django.contrib import admin

from . import views

import contests.urls

from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout,
        {'template_name': 'system/logged_out.html',
        'extra_context': {'redirect_next': '/'}}, name='logout'),
    url(r'^password_change/$', auth_views.password_change,
        {'template_name': 'system/password_change.html'},
        name='password_change'),
    url(r'^password_change/done/$', auth_views.password_change_done,
        {'template_name': 'system/password_changed.html'},
        name='password_change_done'),
    url(r'^password_reset/$', auth_views.password_reset,
        {'template_name': 'system/password_reset.html'},
        name='password_reset'),
    url(r'^password_reset/done/$', auth_views.password_reset_done,
        {'template_name': 'system/password_reset_done.html'},
        name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', auth_views.password_reset_complete,
        name='password_reset_complete'),
    url(r'^$', views.announcements, name="announcements"),
    url(r'^user-settings/$', views.user_settings, name='user_settings'),
    url(r'^', include(contests.urls)),
    url(r'^admin/', include(admin.site.urls)),
]
