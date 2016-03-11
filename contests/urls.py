from django.conf.urls import url

from . import views

app_name = 'contests'
urlpatterns = [
    url(r'^contests/$', views.list, name='list'),
    url(r'^contests/setup/$', views.ContestCreate.as_view(), name='setup_new'),
    url(r'^contest/(?P<contests_code>[-\w]+)/$', views.Description.as_view(),
        name='description'),
    url(r'^contest/(?P<contests_code>[-\w]+)/rules$', views.Rules.as_view(),
        name='rules'),
    url(r'^contest/(?P<contests_code>[-\w]+)/submit/$',
        views.Submit.as_view(), name='submit'),
    url(r'^contest/(?P<contests_code>[-\w]+)/submissions/$',
        views.Submissions.as_view(), name='submissions'),
    url(r'^contest/(?P<contests_code>[-\w]+)/my_submissions/$',
        views.MySubmissions.as_view(), name='my_submissions'),
    url(r'^contest/(?P<contests_code>[-\w]+)/submission/(?P<submission_id>[0-9]+)/$',
        views.SubmissionView.as_view(), name='submission'),
    url(r'^contest/(?P<contests_code>[-\w]+)/rejudge/(?P<submission_id>[0-9]+)/$',
        views.RejudgeView.as_view(), name='rejudge'),
    url(r'^contest/(?P<contests_code>[-\w]+)/rejudge/$',
        views.RejudgeView.as_view(), name='rejudge'),
    url(r'^contest/(?P<contests_code>[-\w]+)/rejudge_done/(?P<submission_id>[0-9]+)/$',
        views.RejudgeDone.as_view(), name='rejudge_done'),
    url(r'^contest/(?P<contests_code>[-\w]+)/rejudge_done/$',
        views.RejudgeDone.as_view(), name='rejudge_done'),
    url(r'^contest/(?P<contests_code>[-\w]+)/setup/$',
        views.ContestUpdate.as_view(), name='setup'),
    url(r'^contest/(?P<contests_code>[-\w]+)/teams/$',
        views.Teams.as_view(), name='teams'),
    url(r'^contest/(?P<contests_code>[-\w]+)/teams/new$',
        views.TeamCreate.as_view(), name='new_team'),
    url(r'^contest/(?P<contests_code>[-\w]+)/team/(?P<team_id>[0-9]+)/$',
        views.TeamView.as_view(), name='team'),
    url(r'^contest/(?P<contests_code>[-\w]+)/team/(?P<team_id>[0-9]+)/join/$',
        views.JoinTeam.as_view, name='join_team'),
    url(r'^contest/(?P<contests_code>[-\w]+)/team/(?P<team_id>[0-9]+)/leave/$',
        views.LeaveTeam.as_view(), name='leave_team'),
    url(r'^contest/(?P<contests_code>[-\w]+)/leaderboard/(?P<stage_id>[0-9]+)/$',
        views.Leaderboard.as_view(), name='leaderboard'),
    url(r'^contest/(?P<contests_code>[-\w]+)/observe/$',
        views.StartObserving.as_view(), name='observe'),
    url(r'^contest/(?P<contests_code>[-\w]+)/unobserve/$',
        views.StopObserving.as_view(), name='unobserve'),
]
