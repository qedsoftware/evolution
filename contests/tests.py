from django.test import TestCase, RequestFactory, Client
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from .models import *
from .views import ContestContext

from system.models import PostData

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
