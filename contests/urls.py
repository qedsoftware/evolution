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
    url(r'^contest/(?P<contests_code>[-\w]+)/'
        r'submission/(?P<submission_id>[0-9]+)/$',
        views.SubmissionView.as_view(), name='submission'),
    url(r'^contest/(?P<contests_code>[-\w]+)/'
        r'submission/(?P<submission_id>[0-9]+)/answer/$',
        views.DownloadSubmissionAnswer.as_view(), name='submission_answer'),
    url(r'^contest/(?P<contests_code>[-\w]+)/'
        r'submission/(?P<submission_id>[0-9]+)/source/$',
        views.DownloadSubmissionSource.as_view(), name='submission_source'),
    url(r'^contest/(?P<contests_code>[-\w]+)/'
        r'rejudge/(?P<submission_id>[0-9]+)/$',
        views.SubmissionRejudgeView.as_view(), name='rejudge'),
    url(r'^contest/(?P<contests_code>[-\w]+)/rejudge/$',
        views.ContestRejudgeView.as_view(), name='rejudge'),
    url(r'^contest/(?P<contests_code>[-\w]+)/setup/$',
        views.ContestUpdate.as_view(), name='setup'),
    url(r'^contest/(?P<contests_code>[-\w]+)/teams/$',
        views.Teams.as_view(), name='teams'),
    url(r'^contest/(?P<contests_code>[-\w]+)/teams/new$',
        views.TeamCreate.as_view(), name='new_team'),
    url(r'^contest/(?P<contests_code>[-\w]+)/team/(?P<team_id>[0-9]+)/$',
        views.TeamView.as_view(), name='team'),
    url(r'^contest/(?P<contests_code>[-\w]+)/team/(?P<team_id>[0-9]+)/join/$',
        views.JoinTeam.as_view(), name='join_team'),
    url(r'^contest/(?P<contests_code>[-\w]+)/'
        r'team/(?P<team_id>[0-9]+)/invite/$',
        views.TeamInvitationView.as_view(), name='invite_to_team'),
    url(r'^contest/(?P<contests_code>[-\w]+)/team/(?P<team_id>[0-9]+)/leave/$',
        views.LeaveTeam.as_view(), name='leave_team'),
    url(r'^contest/(?P<contests_code>[-\w]+)/public_leaderboard/$',
        views.PublicLeaderboard.as_view(), name='public_leaderboard'),
    url(r'^contest/(?P<contests_code>[-\w]+)/final_leaderboard/$',
        views.TestLeaderboard.as_view(), name='test_leaderboard'),
    url(r'^contest/(?P<contests_code>[-\w]+)/observe/$',
        views.StartObserving.as_view(), name='observe'),
    url(r'^contest/(?P<contests_code>[-\w]+)/unobserve/$',
        views.StopObserving.as_view(), name='unobserve'),
    url(r'^contest/(?P<contests_code>[-\w]+)/'
        r'submission/(?P<submission_id>[0-9]+)/select/$',
        views.SelectSubmission.as_view(), name='select_submission'),
    url(r'^contest/(?P<contests_code>[-\w]+)/'
        r'submission/(?P<submission_id>[0-9]+)/unselect/$',
        views.UnselectSubmission.as_view(), name='unselect_submission'),
    url(r'^contests/admin_hints/$', views.ContestAdminHints.as_view(),
        name='admin_hints'),
]
