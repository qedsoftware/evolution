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
    url(r'^contest/(?P<contests_code>[-\w]+)/submit/$',
        views.Submit.as_view(), name='submit'),
    url(r'^contest/(?P<contests_code>[-\w]+)/submissions/$',
        views.Submissions.as_view(), name='submissions'),
    url(r'^contest/(?P<contests_code>[-\w]+)/submission/(?P<submission_id>[0-9]+)/$',
        views.submission, name='submission'),
    url(r'^contest/(?P<contests_code>[-\w]+)/rejudge/(?P<submission_id>[0-9]+)/$',
        views.rejudge_view, name='rejudge'),
    url(r'^contest/(?P<contests_code>[-\w]+)/rejudge/$',
        views.rejudge_view, name='rejudge'),
    url(r'^contest/(?P<contests_code>[-\w]+)/rejudge_done/(?P<submission_id>[0-9]+)/$',
        views.rejudge_done, name='rejudge_done'),
    url(r'^contest/(?P<contests_code>[-\w]+)/rejudge_done/$',
        views.rejudge_done, name='rejudge_done'),
    url(r'^contest/(?P<contests_code>[-\w]+)/setup/$',
        views.ContestUpdate.as_view(), name='setup'),
    url(r'^contest/(?P<contests_code>[-\w]+)/teams/$',
        views.TeamList.as_view(), name='teams'),
    url(r'^contest/(?P<contests_code>[-\w]+)/teams/new$',
        views.CreateTeam.as_view(), name='new_team'),
    url(r'^contest/(?P<contests_code>[-\w]+)/team/(?P<team_id>[0-9]+)/$',
        views.team, name='team'),
    url(r'^contest/(?P<contests_code>[-\w]+)/team/(?P<team_id>[0-9]+)/join/$',
        views.join_team, name='join_team'),
    url(r'^contest/(?P<contests_code>[-\w]+)/team/(?P<team_id>[0-9]+)/leave/$',
        views.leave_team, name='leave_team'),
]
