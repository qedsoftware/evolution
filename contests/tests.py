from django.test import TestCase, RequestFactory, Client
from django_webtest import WebTest
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from datetime import timedelta

from .models import *
from .views import ContestContext

from system.tests import new_user
from grading.tests import script_always_42

from system.models import PostData

future_time = timezone.now() + timedelta(weeks=1)
past_time = timezone.now() - timedelta(weeks=1)


class ContestFactoryTest(TestCase):

    def empty_description(self):
        factory = ContestFactory()
        factory.name = "empty"
        factory.code = "empty"
        factory.description = ""
        contest = factory.create()
        self.assertEqual(contest.description, '')

    def example_contest(self):
        factory = ContestFactory()
        factory.name = "contest name"
        factory.code = "contest_code"
        factory.description = PostData.from_source("test", "html")
        factory.description.build_html()
        factory.rules = factory.description
        factory.scoring_script = ContentFile('from __future__ import skynet')
        factory.bigger_better = False
        factory.verification_begin = timezone.now()
        factory.verification_end = timezone.now()
        factory.answer_for_verification = ContentFile('bla')
        factory.test_begin = timezone.now()
        factory.test_end = timezone.now()
        factory.answer_for_test = ContentFile('blabla')
        factory.published_final_results = False
        factory.selected_limit = 17
        return factory.create()

    def assert_example(self, contest):
        self.assertEqual(str(contest), 'contest_code')
        self.assertTrue('contest_code' in repr(contest))
        self.assertEqual(contest.code, "contest_code")
        self.assertEqual(contest.name, "contest name")
        self.assertEqual(contest.description.html, 'test')
        self.assertEqual(contest.rules.html, 'test')
        verification = contest.verification_stage
        test = contest.test_stage
        self.assertEqual(verification.grader.scoring_script,
                         test.grader.scoring_script)
        scoring_script = verification.grader.scoring_script
        self.assertEqual(scoring_script.source.read(),
                         b'from __future__ import skynet')
        self.assertEqual(verification.grader.answer.read(), b'bla')
        self.assertEqual(test.grader.answer.read(), b'blabla')
        self.assertEqual(verification.published_results, True)
        self.assertEqual(test.published_results, False)
        self.assertEqual(verification.requires_selection, False)
        self.assertEqual(test.requires_selection, True)
        self.assertEqual(test.selected_limit, 17)

    def test_create(self):
        self.example_contest()
        from_db = Contest.objects.get()
        self.assert_example(from_db)

    def test_from_dict(self):
        description = PostData.from_source("test", "plaintext")
        description.build_html()
        factory = ContestFactory.from_dict({
            'name': 'contest name',
            'code': 'contest_code',
            'description': description,
            'rules': description,
            'scoring_script': ContentFile('from __future__ import skynet'),
            'bigger_better': False,
            'verification_begin': timezone.now(),
            'verification_end': timezone.now(),
            'answer_for_verification': ContentFile('bla'),
            'test_begin': timezone.now(),
            'test_end': timezone.now(),
            'answer_for_test': ContentFile('blabla'),
            'published_final_results': False,
            'selected_limit': 17
        })
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

    def simple_test(self):
        context = ContestContext(self.admin_user, self.contest)
        self.assertTrue(context.is_contest_admin)
        self.assertIsNone(context.user_team)

    def test_team_in_another_contest(self):
        join_team(self.regular_user, self.another_team)
        context = ContestContext(self.regular_user, self.contest)
        self.assertIsNone(context.user_team)
        context = ContestContext(self.regular_user, self.another_contest)
        self.assertEqual(context.user_team, self.another_team)


class Teams(WebTest):
    def setUp(self):
        standard_base(self)

    def test_teams(self):
        page = self.app.get(reverse('contests:teams',
            args=['contest']), user='user')
        page.mustcontain('Teams', 'new team')


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
        self.assertContains(response, 'No members')


def submit_with_score(team, stage, score, selected=False):
    cs = ContestSubmission()
    cs.stage = stage
    submission = Submission.create(stage.grader, ContentFile('mock_file'))
    submission.score = score
    submission.save()
    cs.selected = selected
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
        self.team_d = Team(contest=self.contest, name='D')
        self.team_d.save()
        self.team_c = Team(contest=self.contest, name='C')
        self.team_c.save()
        self.teams = [self.team_d, self.team_c, self.team_b, self.team_a]
        self.empty_contest = ContestFactory.from_dict({
            'name': 'Empty',
            'code': 'empty'
        }).create()

    def test_no_submissions(self):
        # all the submissions are trivial
        entries = build_leaderboard(self.contest, self.contest.test_stage)
        for entry in entries:
            self.assertEqual(entry.position, 1)
            self.assertIsNone(entry.score)
            self.assertIsNone(entry.submission)
            self.assertIsNotNone(entry.team)
            self.assertEqual(entry.team.member_list, [])
        self.assertEqual(entries, [])

    def test_alphabetic_order(self):
        for team in self.teams:
            cs = submit_with_score(team, self.contest.test_stage, 42,
                                   selected=True)
            self.assertEqual(cs.team, team)
            self.assertEqual(cs.submission.score, 42)
        entries = build_leaderboard(self.contest, self.contest.test_stage)
        for entry in entries:
            self.assertEqual(entry.position, 1)
            self.assertEqual(entry.score, 42)
            self.assertIsNotNone(entry.submission)
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
        entries = build_leaderboard(self.empty_contest,
            self.empty_contest.verification_stage)
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
        form = page.forms['create-contest-form']
        form['name'] = name
        form['code'] = 'contest-code'
        page = form.submit().follow()
        # update contest
        contest = Contest.objects.get()
        self.assertEqual(contest.code, 'contest-code')
        self.assertEqual(contest.name, name)
        page.mustcontain('created contest', 'Contest Settings', name)
        form = page.forms['contest-settings-form']
        form['bigger_better'] = False
        form['published_final_results'] = True
        self.assertEqual(contest.bigger_better, True)
        self.assertEqual(contest.verification_stage.published_results, True)
        self.assertEqual(contest.test_stage.published_results, False)
        page = form.submit().follow()
        page.mustcontain('Successfully updated')
        contest = Contest.objects.get()
        self.assertEqual(contest.code, 'contest-code')
        self.assertEqual(contest.bigger_better, False)
        self.assertEqual(contest.verification_stage.published_results, True)
        self.assertEqual(contest.test_stage.published_results, True)


class MinimalContestSetup(WebTest):
    def setUp(self):
        self.admin = new_user('admin', admin=True)

    def test(self):
        # add a contest
        page = self.app.get(reverse('contests:setup_new'), user='admin')
        self.assertContains(page, 'New Contest')
        self.assertContains(page, 'Create')
        name = 'contest name'
        form = page.forms['create-contest-form']
        form['name'] = name
        form['code'] = 'contest-code'
        page = form.submit().follow()
        form = page.forms['contest-settings-form']
        page = form.submit().follow()
        page.mustcontain('Successfully updated')
        contest = Contest.objects.get()
        self.assertEqual(contest.code, 'contest-code')
        self.assertEqual(contest.bigger_better, True)
        self.assertEqual(contest.verification_stage.published_results, True)
        self.assertEqual(contest.test_stage.published_results, False)


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
            'test_end': past_time,
            'scoring_script': ContentFile(script_always_42),
            'answer_for_verification': ContentFile('meh')
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
        submit_form = page.forms['submit-form']
        submit_form['stage'] = '1'  # verification
        submit_form['output_file'] = 'output', b'output_data'
        submit_form['source_code'] = 'source', b'source_data'
        submit_form['comment'] = ''
        page = submit_form.submit().follow()
        self.assertEqual(ContestSubmission.objects.count(), 1)
        cs = ContestSubmission.objects.get()
        self.assertEqual(cs.stage, self.contest.verification_stage)
        self.assertEqual(cs.team, self.team)
        self.assertEqual(cs.comment, '')
        self.assertEqual(cs.submission.output.read(), b'output_data')
        self.assertEqual(cs.source.read(), b'source_data')


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
        page = page.forms['rejudge-all'].submit().follow()
        page.mustcontain('All submissions', 'marked for rejudging')

    def test_rejudge_user(self):
        unauthorized_get(self.app,
            reverse('contests:rejudge', args=['contest']),
            user=self.user)

    def test_rejudge_single(self):
        submission = submit_with_score(None, self.contest.test_stage, 42)
        page = self.app.get(reverse('contests:submission',
            args=[self.contest.code, submission.id]), user='admin')
        page = page.forms['rejudge-single'].submit().follow()
        page.mustcontain('Submission', str(submission.id),
            'marked for rejudging')


class TeamInvitationExpiryTest(TestCase):
    def test(self):
        invitation = TeamInvitation()
        invitation.created_at = timezone.now()
        self.assertFalse(invitation.is_expired())


class TeamInvitationTest(WebTest):
    def setUp(self):
        standard_base(self)
        self.team = Team(contest=self.contest, name='Team')
        self.team.save()
        join_team(self.user, self.team)
        self.user2 = new_user('another_user')
        self.user3 = new_user('yet_another_user')

    def accept_invitation_page(self, invitation_url, user=None):
        return self.app.get(invitation_url, user=user). \
            forms['join_team'].submit().follow()

    def test_no_code_join(self):
        # it should fail with an error
        url = reverse('contests:join_team', args=['contest', self.team.id])
        page = self.accept_invitation_page(url, user=self.user)
        page.mustcontain('Invalid Secret Code')

    def test_invite(self):
        page = self.app.get(reverse('contests:invite_to_team',
            args=['contest', self.team.id]), user=self.user)
        link_copy_form_html = page.html.find(id='team-invitation-link')
        invitation_url = link_copy_form_html.input['value']
        invitation = TeamInvitation.objects.get()
        self.assertEqual(invitation.invited_by, self.user)
        self.assertFalse(invitation.accepted)
        self.assertTrue(invitation.secret_code in invitation_url)
        # already in this team
        page = self.accept_invitation_page(invitation_url, user=self.user)
        page.mustcontain('Cannot join')
        invitation.refresh_from_db()
        self.assertFalse(invitation.accepted)
        self.assertIsNone(invitation.accepted_by)

        # second user steps in
        page = self.accept_invitation_page(invitation_url, user=self.user2)
        invitation.refresh_from_db()
        self.assertEqual(invitation.accepted_by, self.user2)
        self.assertTrue(invitation.accepted)
        self.assertTrue(in_team(self.user2, self.team))

        # third user tries to use this inviation again
        page = self.accept_invitation_page(invitation_url, user=self.user3)
        page.mustcontain('already', 'used')
        self.assertFalse(in_team(self.user3, self.team))
        invitation.refresh_from_db()
        self.assertEqual(invitation.accepted_by, self.user2)
