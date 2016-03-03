from django.conf.urls import url

from . import views

app_name = 'contests'
urlpatterns = [
    url(r'^contests/$', views.list, name='list'),
    url(r'^contests/setup/$', views.ContestCreate.as_view(), name='setup_new'),
    url(r'^contest/(?P<contests_code>[-\w]+)/$', views.description,
        name='description'),
    url(r'^contest/(?P<contests_code>[-\w]+)/rules$', views.rules,
        name='rules'),
    url(r'^contest/(?P<contests_code>[-\w]+)/submit/$', views.Submit.as_view(),
        name='submit'),
    url(r'^contest/(?P<contests_code>[-\w]+)/submissions/$', views.Submissions.as_view(),
        name='submissions'),
    #url(r'^contest/(?P<contests_code>[-\w]+)/setup/$', views.ContestUpdate.as_view(),
    #    name='setup'),
]
