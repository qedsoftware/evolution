from django.test import TestCase, RequestFactory, Client
from django_webtest import WebTest
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from datetime import timedelta

from .models import *
from .views import ContestContext

from system.models import PostData

future_time = timezone.now() + timedelta(weeks=1)
past_time = timezone.now() - timedelta(weeks=1)

class ContestFactoryTest(TestCase):

    def example_contest(self):
        factory = ContestFactory()
        factory.name = "contest name"
        factory.code = "contest_code"
        factory.description = PostData.from_source("test", "html")
        factory.description.build_html()
        factory.rules = factory.description
        factory.verification_begin = timezone.now()
        factory.verification_end = timezone.now()
        return factory.create()

    def assert_example(self, contest):
        self.assertEqual(contest.code, "contest_code")
        self.assertEqual(contest.name, "contest name")
        self.assertEqual(contest.description.html, 'test')
        self.assertEqual(contest.rules.html, 'test')

    def test_create(self):
        self.example_contest()
        from_db = Contest.objects.get()
        self.assert_example(from_db)

    def test_from_dict(self):
        description = PostData.from_source("test", "plaintext")
        description.build_html()
        factory = ContestFactory.from_dict({'name': 'contest name',
            'code': 'contest_code', 'description': description,
            'rules': description, 'verification_begin': timezone.now(),
            'verification_end': timezone.now()})
        factory.create()
        from_db = Contest.objects.get()
        self.assert_example(from_db)

    def test_update(self):
        contest = self.example_contest()
        factory = ContestFactory.from_dict({
            'name': 'test'
        })
        factory.update(contest)
        self.assertEqual(contest.code, "contest_code")
        self.assertEqual(contest.name, "test")
        self.assertEqual(contest.description.html, 'test')
        self.assertEqual(contest.rules.html, 'test')


def new_user(username, admin=False):
    user = User.objects.create_user(username, username + '@example.com',
            'password')
    user.first_name = username
    user.last_name = username + 'son'
    if admin:
        user.is_superuser = True
        user.is_staff = True
    user.save()
    return user

class ContestContextTest(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.regular_user = new_user('regular_user')
        self.admin_user = new_user('admin_user', admin=True)
        self.contest = ContestFactory.from_dict({
            'name': 'Contest',
            'code': 'contest'
        }).create()
        self.another_contest = ContestFactory.from_dict({
            'name': 'AnotherContest',
            'code': 'another_contest'
        }).create()
        self.team = Team(contest=self.contest, name='team')
        self.team.save()
        self.another_team = Team(contest=self.another_contest,
            name='another_team')
        self.another_team.save()

    def request(self, user=None):
        request = self.request_factory.get('/something')
        request.user = user
        return request

    def user_context(self, user=None, contest=None):
        request = self.request(user=user)
        return ContestContext(request, contest)

    def simple_test(self):
        context = self.user_context(user=self.admin_user, contest=self.contest)
        self.assertTrue(context.is_contest_admin)
        self.assertIsNone(context.user_team)

    def test_team_in_another_contest(self):
        join_team(self.regular_user, self.another_team)
        context = self.user_context(user=self.regular_user,
            contest=self.contest)
        self.assertIsNone(context.user_team)
        context = self.user_context(user=self.regular_user,
            contest=self.another_contest)
        self.assertEqual(context.user_team, self.another_team)

class TeamViewTests(TestCase):
    def setUp(self):
        self.alice = new_user('alice')
        self.bob = new_user('bob')
        self.carol = new_user('carol')
        self.contest = ContestFactory.from_dict({
            'name': 'Contest',
            'code': 'contest'
        }).create()
        self.another_contest = ContestFactory.from_dict({
            'name': 'AnotherContest',
            'code': 'another_contest'
        }).create()
        self.team_a = Team(contest=self.contest, name='Team A')
        self.team_a.save()
        self.team_b = Team(contest=self.contest, name='Team B')
        self.team_b.save()
        self.another_contest_team = Team(contest=self.another_contest,
            name='another_team')
        self.another_contest_team.save()
        self.client = Client()
        self.client.force_login(self.alice)

    def test_list(self):
        join_team(self.alice, self.team_a)
        join_team(self.bob, self.team_a)
        join_team(self.carol, self.another_contest_team)
        response = self.client.get(reverse('contests:teams',
            args=[self.contest.code]))
        self.assertContains(response, 'alice aliceson', count=1)
        self.assertContains(response, 'bob bobson', count=1)
        self.assertNotContains(response, 'carol carolson')
        self.assertContains(response, 'Team A', count=1)
        self.assertContains(response, 'Team B', count=1)
        team_0 = response.context['teams'][0]
        team_1 = response.context['teams'][1]
        self.assertEqual(team_0, self.team_a)
        self.assertEqual(team_1, self.team_b)
        self.assertEqual(team_1.member_list, [])
        self.assertContains(response, 'no members')

def submit_with_score(team, stage, score):
    cs = ContestSubmission()
    cs.stage = stage
    submission = Submission.create(stage.grader, ContentFile('mock_file'))
    submission.score = score
    submission.save();
    cs.submission = submission
    cs.team = team
    cs.save()
    return cs

class LeaderboardTest(TestCase):
    def setUp(self):
        self.contest = ContestFactory.from_dict({
            'name': 'Contest',
            'code': 'contest'
        }).create()
        # non-alphabetic order
        self.team_b = Team(contest=self.contest, name='B')
        self.team_b.save()
        self.team_a = Team(contest=self.contest, name='A')
        self.team_a.save()
        self.team_d= Team(contest=self.contest, name='D')
        self.team_d.save()
        self.team_c= Team(contest=self.contest, name='C')
        self.team_c.save()
        self.empty_contest = ContestFactory.from_dict({
            'name': 'Empty',
            'code': 'empty'
        }).create()

    def test_no_submissions(self):
        entries = build_leaderboard(self.contest, self.contest.test_stage)
        for entry in entries:
            self.assertEqual(entry.position, 1)
            self.assertIsNone(entry.score)
            self.assertIsNone(entry.submission)
            self.assertIsNotNone(entry.team)
            self.assertEqual(entry.team.member_list, [])
        self.assertEqual([e.team.name for e in entries], ['A', 'B', 'C', 'D'])

    def test_empty_contest(self):
        entries_test = build_leaderboard(self.empty_contest,
            self.empty_contest.test_stage)
        self.assertEqual(entries_test, [])
        entries_verification = build_leaderboard(self.empty_contest,
            self.empty_contest.verification_stage)
        self.assertEqual(entries_verification, [])

    def test_admin_submission(self):
        data = SubmissionData()
        data.output = ''
        submit_with_score(None, self.empty_contest.verification_stage, 42)
        entries = build_leaderboard(self.empty_contest, self.empty_contest.verification_stage)
        self.assertEqual(entries, [])

class EmptyContestListTest(TestCase):
    def setUp(self):
        self.user = new_user('user')

    def test(self):
        client = Client()
        client.force_login(self.user)
        response = client.get(reverse('contests:list'))
        self.assertContains(response, 'Contests')

class ContestCreateAndSetupTest(WebTest):
    def setUp(self):
        self.admin = new_user('admin', admin=True)

    def test(self):
        # add a contest
        page = self.app.get(reverse('contests:setup_new'), user='admin')
        self.assertContains(page, 'New Contest')
        self.assertContains(page, 'Create')
        name = 'contest name'
        page.form['name'] = name
        page.form['code'] = 'contest-code'
        page = page.form.submit().follow()
        contest = Contest.objects.get()
        self.assertEqual(contest.code, 'contest-code')
        self.assertEqual(contest.name, name)
        page.mustcontain('created contest', 'Contest Settings', name)
        form = page.forms[1] # TODO, give it proper id
        form['bigger_better'] = False
        form['published_final_results'] = True
        self.assertEqual(contest.bigger_better, True);
        self.assertEqual(contest.verification_stage.published_results, True)
        self.assertEqual(contest.test_stage.published_results, False)
        page = form.submit().follow()
        page.mustcontain('Successfully updated')
        contest = Contest.objects.get()
        self.assertEqual(contest.code, 'contest-code')
        self.assertEqual(contest.bigger_better, False);
        self.assertEqual(contest.verification_stage.published_results, True)
        self.assertEqual(contest.test_stage.published_results, True)

class RulesAndDescriptionTest(WebTest):
    def setUp(self):
        self.user = new_user('user')
        description = PostData.from_source('__description__', 'html')
        description.build_html()
        rules = PostData.from_source('__rules__', 'html')
        rules.build_html()
        ContestFactory.from_dict({
            'name': 'Contest',
            'code': 'contest',
            'description': description,
            'rules': rules
        }).create()

    def test_description(self):
        page = self.app.get(reverse('contests:description', args=['contest']),
            user='user')
        page.mustcontain('Description', '__description__')

    def test_rules(self):
        page = self.app.get(reverse('contests:rules', args=['contest']),
            user='user')
        page.mustcontain('Rules', '__rules__')


ACCESS_DENIED = "You don't have access"

class SubmitTest(WebTest):
    def setUp(self):
        self.user = new_user('user')
        self.contest = ContestFactory.from_dict({
            'name': 'Contest',
            'code': 'contest',
            'verification_begin': past_time,
            'verification_end': future_time,
            'test_begin': past_time,
            'test_end': past_time
        }).create()
        self.team = Team(contest=self.contest, name='Team')
        self.team.save()
        join_team(self.user, self.team)

    def test_anon_submit(self):
        page = self.app.get(reverse('contests:submit',
            args=[self.contest.code]))
        page = page.follow()
        page.mustcontain('log in')

    def test_submit(self):
        page = self.app.get(reverse('contests:submit',
            args=[self.contest.code]), user='user')
        page.mustcontain('Send Submission')

class MySubmissionsTest(WebTest):
    def setUp(self):
        self.user = new_user('user')
        self.user_no_team = new_user('user_no_team')
        self.contest = ContestFactory.from_dict({
            'name': 'Contest',
            'code': 'contest',
        }).create()
        self.team = Team(contest=self.contest, name='Team')
        self.team.save()
        join_team(self.user, self.team)

    def test_my_submissions_no_team(self):
        unauthorized_get(self.app,
            reverse('contests:my_submissions', args=['contest']),
            user=self.user_no_team)

    def test_my_submissions(self):
        page = self.app.get(reverse('contests:my_submissions',
            args=['contest']), user='user')
        page.mustcontain('My Submissions')

def unauthorized_get(app, url, user):
    page = app.get(url, user=user.username)
    page = page.follow()
    page.mustcontain(ACCESS_DENIED)

def standard_base(test_obj):
    test_obj.user = new_user('user')
    test_obj.admin = new_user('admin', admin=True)
    test_obj.contest = ContestFactory.from_dict({
        'name': 'Contest',
        'code': 'contest',
    }).create()

class SubmissionsTest(WebTest):
    def setUp(self):
        standard_base(self)
        self.team = Team(contest=self.contest, name='Team')
        self.team.save()
        join_team(self.user, self.team)

    def test_submissions_user(self):
        unauthorized_get(self.app,
            reverse('contests:submissions', args=['contest']),
            user=self.user)

    def test_submissions(self):
        page = self.app.get(reverse('contests:submissions',
            args=['contest']), user='admin')
        page.mustcontain('Submissions')

class RejudgeTest(WebTest):
    def setUp(self):
        standard_base(self)

    def test_rejudge(self):
        page = self.app.get(reverse('contests:rejudge',
            args=['contest']), user='admin')
        page.mustcontain('Rejudge All Submissions')
        page = page.form.submit().follow()
        page.mustcontain('All submissions', 'marked for rejudging')

    def test_rejudge_user(self):
        unauthorized_get(self.app,
            reverse('contests:rejudge', args=['contest']),
            user=self.user)

    def test_rejudge_single(self):
        submission = submit_with_score(None, self.contest.test_stage, 42)
        page = self.app.get(reverse('contests:submission',
            args=[self.contest.code, submission.id]), user='admin')
        page = page.form.submit().follow()
        page.mustcontain('Submission', str(submission.id),
            'marked for rejudging')

class Teams(WebTest):
    def setUp(self):
        standard_base(self)

    def test_teams(self):
        page = self.app.get(reverse('contests:teams',
            args=['contest']), user='user')
        page.mustcontain('Teams', 'new team')
