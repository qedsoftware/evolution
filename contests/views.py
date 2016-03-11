from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.views.generic.base import ContextMixin, TemplateView, \
    RedirectView, View
from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.views.generic.edit import FormView, CreateView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.contrib import messages
from django.utils.safestring import mark_safe

from system.views import title

from .models import Contest, ContestFactory, ContestSubmission, \
    SubmissionData, submit, ContestStage, rejudge_submission, \
    rejudge_contest, Team, TeamMember, join_team as join_team_action, \
    leave_team as leave_team_action, can_join_team, in_team, \
    is_contest_admin, teams_with_member_list, build_leaderboard, user_team, \
    can_create_team

from .forms import ContestForm, ContestCreateForm, SubmitForm

from base.models import GradingAttempt

class ContestContext:
    # TODO move to model
    """ Common data, required by all contest views. """
    user = None
    contest = None
    is_contest_admin = None
    can_submit = None
    can_create_team = None
    can_see_team_submissions = None
    can_see_all_submissions = None
    can_see_verification_leaderboard = None
    can_see_test_leaderboard = None
    user_team = None
    is_observing = None

    repr_attributes = [
        'user',
        'user_team',
        'contest',
        'is_contest_admin',
        'can_submit',
        'can_create_team',
        'can_see_team_submissions',
        'can_see_all_submissions',
        'can_see_verification_leaderboard',
        'can_see_test_leaderboard',
        'is_observing'
    ]

    def __init__(self, request, contest):
        self.contest = contest
        self.user = request.user
        # we want it to be a model - so we can query easier
        if not self.user.is_authenticated():
            self.user = None
        self.user_team = user_team(self.user, contest)
        self.is_contest_admin = is_contest_admin(self.user, contest)
        self.can_create_team = can_create_team(self.user, contest)
        self.can_see_team_submissions = self.user_team is not None
        self.can_see_all_submissions = self.is_contest_admin
        self.can_submit = self.user_team is not None or self.is_contest_admin
        self.can_see_verification_leaderboard = \
            self.can_see_stage_leaderboard(contest.verification_stage)
        self.can_see_test_leaderboard = \
            self.can_see_stage_leaderboard(contest.test_stage)
        self.is_observing = contest.observing.filter(id=self.user.id).exists()

    def can_see_submission(self, submission):
        return is_contest_admin(self.user, self.contest) or \
            (submission.team is not None and submission.team == self.user_team)

    def can_see_stage_leaderboard(self, stage):
        return self.is_contest_admin or stage.published_results

    def __repr__(self):
        result = ['<ContestContext:']
        first = True
        for attr in self.repr_attributes:
            if not first:
                result.append(', ')
            first = False
            result.append(attr + ': ' + repr(getattr(self, attr, '?')))
        result.append('>')
        return ''.join(result)


def contest_title(contest, text = None):
    return ' - '.join(filter(None, [contest.name, text]))


class ContestMixin(object):
    """
    Common logic for views within a Contest

    Uses:
        contest_related - iterable of fields that will be
            select_related for contest
    """

    contest_related = []

    _contest = None
    _contest_context = None

    title = None

    @property
    def contest_code(self):
        return self.kwargs['contests_code']

    @property
    def contest_context(self):
        if not self._contest_context:
            self._contest_context = ContestContext(self.request, self.contest)
        return self._contest_context

    @property
    def contest(self):
        if not self._contest:
            contest_qs = Contest.objects.filter(code=self.contest_code)
            for related in self.contest_related:
                contest_qs = contest_qs.select_related(related)
            self._contest = contest_qs.get()
        return self._contest

    def get_context_data(self, **kwargs):
        context = super(ContestMixin, self).get_context_data()
        context['contest'] = self.contest
        context['contest_context'] = self.contest_context
        context['title'] = contest_title(self.contest, self.title)
        return context


@login_required
def list(request):
    my_memberships = TeamMember.objects.filter(user=request.user). \
        select_related('contest').select_related('team')

    observed_contests = request.user.observed_contests.all()

    all_contests = Contest.objects.all()
    paginator = Paginator(all_contests, 10)

    page = request.GET.get('page')
    try:
        contests= paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        contests = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        contests = paginator.page(paginator.num_pages)

    return render(request, 'contests/list.html', {
        'contests': contests,
        'my_memberships': my_memberships,
        'observed_contests': observed_contests
    })


class ContestCreate(LoginRequiredMixin, FormView):
    form_class = ContestCreateForm
    template_name = "contests/contest_create_form.html"

    contest = None

    def get_context_data(self):
        context = super(ContestCreate, self).get_context_data()
        context['title'] = 'New Contest'
        return context

    def form_valid(self, form):
        factory = ContestFactory.from_dict(form.cleaned_data)
        self.code = form.cleaned_data['code']
        contest = factory.create()
        contest.observing.add(self.request.user)
        self.contest = contest
        return super(ContestCreate, self).form_valid(form)

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS,
            mark_safe('You have created contest <em>%s</em>. '
                'Now you can start setting it up.'
                % self.contest.name))
        return reverse('contests:setup', args=[self.code])


class ContestUpdate(UserPassesTestMixin, ContestMixin, FormView):
    form_class = ContestForm
    template_name = "contests/contest_form.html"
    title = "Settings"

    def test_func(self):
        return self.contest_context.is_contest_admin

    def get_code(self):
        return self.kwargs['contests_code']

    def get_initial(self):
        initial = super(ContestUpdate, self).get_initial()
        contest = Contest.objects. \
            select_related('description'). \
            select_related('rules'). \
            select_related('verification_stage'). \
            select_related('test_stage'). \
            get(code=self.get_code())
        initial['name'] = contest.name
        initial['code'] = contest.code
        initial['description'] = contest.description.source
        initial['rules'] = contest.rules.source
        initial['scoring_script'] = contest.scoring_script.source
        initial['bigger_better'] = contest.bigger_better
        initial['answer_for_verification'] = contest.verification_stage. \
            grader.answer
        initial['answer_for_test'] = contest.test_stage. \
            grader.answer
        initial['verification_begin'] = contest.verification_stage.begin
        initial['verification_end'] = contest.verification_stage.end
        initial['test_begin'] = contest.test_stage.begin
        initial['test_end'] = contest.test_stage.end
        initial['published_final_results'] = \
            contest.test_stage.published_results
        return initial

    def get_context_data(self, **kwargs):
        context = super(ContestUpdate, self).get_context_data()
        contest = Contest.objects.get(code=self.get_code())
        context['contest'] = contest
        context['contest_context'] = ContestContext(self.request, contest)
        return context

    def form_valid(self, form):
        factory = ContestFactory.from_dict(form.cleaned_data)
        if form.cleaned_data['scoring_script']:
            factory.scoring_script = self.request.FILES.get('scoring_script')
        else:
            factory.scoring_script = False
        if form.cleaned_data['answer_for_verification']:
            factory.answer_for_verification = \
                self.request.FILES.get('answer_for_verification')
        else:
            factory.answer_for_verification = False
        if form.cleaned_data['answer_for_test']:
            factory.answer_for_test = \
                self.request.FILES.get('answer_for_test')
        else:
            factory.answer_for_test = False
        factory.update(self.contest)
        self.contest.observing.add(self.request.user)
        self.contest.save()
        return super(ContestUpdate, self).form_valid(form)

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS,
            'Successfully updated contest settings.')
        return reverse('contests:setup', args=[self.contest.code])


class Description(LoginRequiredMixin, ContestMixin, TemplateView):
    template_name = "system/title_and_text.html"
    title = "Description"

    def get_context_data(self, **kwargs):
        context = super(Description, self).get_context_data()
        context['content_title'] = 'Description'
        context['text'] = self.contest.description.html
        return context


class Rules(LoginRequiredMixin, ContestMixin, TemplateView):
    template_name = "system/title_and_text.html"
    title = "Rules"

    def get_context_data(self, **kwargs):
        context = super(Rules, self).get_context_data()
        context['content_title'] = 'Rules'
        context['text'] = self.contest.rules.html
        return context


class Submit(UserPassesTestMixin, ContestMixin, FormView):
    form_class = SubmitForm
    template_name = "contests/submit_form.html"
    title = "Submit"

    code = None

    def test_func(self):
        return self.contest_context.can_submit

    def get_success_url(self):
        return reverse('contests:submissions',
            args=[self.contest.code])

    def get_stage(self, form):
        stage_name = form.cleaned_data['stage']
        if stage_name == 'verification':
            return self.contest.verification_stage
        elif stage_name == 'test':
            return self.contest.test_stage

    def form_valid(self, form):
        data = SubmissionData()
        data.output = self.request.FILES['output_file']
        stage = self.get_stage(form)
        # TODO move to model
        team = self.contest_context.user_team
        if team is None and not self.contest_context.is_contest_admin:
            raise PermissionDenied()
        submit(team, stage, data)
        return super(Submit, self).form_valid(form)


class Submissions(UserPassesTestMixin, ContestMixin, ListView):
    context_object_name = 'submissions'
    template_name = "contests/submissions.html"
    paginate_by = 10
    title = "Submissions"

    def test_func(self):
        return self.contest_context.is_contest_admin

    def get_queryset(self):
        return ContestSubmission.objects. \
            filter(stage__contest=self.contest)


def ensure_submission_contest_match(submission, contest):
    if submission.stage.contest != contest:
        raise PermissionDenied()


class SubmissionView(UserPassesTestMixin, ContestMixin, TemplateView):
    template_name = 'contests/submission.html'

    _contest_submission = None

    @property
    def contest_submission(self):
        if not self._contest_submission:
            submission_id = self.kwargs['submission_id']
            self._contest_submission = ContestSubmission.objects. \
                select_related('submission').get(id=submission_id)
            ensure_submission_contest_match(self._contest_submission,
                self.contest)
        return self._contest_submission

    @property
    def title(self):
        return "Submission " + str(self.contest_submission.id)

    def test_func(self):
        return self.contest_context.can_see_submission(self.contest_submission)

    def rejudge_url(self):
        return reverse('contests:rejudge',
            args=[self.contest.code, self.contest_submission.id]) + \
            '?next=' + self.request.path

    def get_context_data(self, **kwargs):
        context = super(SubmissionView, self).get_context_data()
        cs = self.contest_submission
        submission = self.contest_submission.submission
        grading_history = GradingAttempt.objects. \
            filter(submission=submission).order_by('-created_at').all()
        context['contest_submission'] = cs
        context['submission'] = submission
        context['grading_history'] = grading_history
        context['rejudge_url'] = self.rejudge_url()
        return context

class MySubmissions(UserPassesTestMixin, ContestMixin, ListView):
    context_object_name = 'submissions'
    template_name = "contests/submissions.html"
    paginate_by = 10
    title = "My Submissions"

    def test_func(self):
        return self.contest_context.is_contest_admin or \
            self.contest_context.user_team is not None

    def get_queryset(self):
        return ContestSubmission.objects.filter(
            team=self.contest_context.user_team)


class RejudgeView(UserPassesTestMixin, ContestMixin, ContextMixin, View):
    # TODO maybe split into separate views for single or massive rejudge.
    template_name = 'contests/rejudge_all.html'
    title = "Rejudge"

    def test_func(self):
        return self.contest_context.is_contest_admin

    @property
    def submission_id(self):
        return self.kwargs.get('submission_id')

    def get(self, request, *args, **kwargs):
        if self.submission_id:
            return redirect(reverse('contests:submission',
                args=[self.contest.code, submission_id]))
        else:
            context = self.get_context_data()
            return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if self.submission_id:
            contest_submission = ContestSubmission.objects. \
                get(id=self.submission_id)
            ensure_submission_contest_match(contest_submission, self.contest)
            rejudge_submission(contest_submission)
            next = request.GET.get('next',
                default=reverse('contests:rejudge_done',
                    args=[self.contest.code, self.submission_id]))
        else:
            rejudge_contest(self.contest)
            next = request.GET.get('next',
                default=reverse('contests:rejudge_done',
                    args=[self.contest.code]))
        return redirect(next)


class RejudgeDone(LoginRequiredMixin, ContestMixin, TemplateView):
    template_name = "contests/rejudge_done.html"
    title = "Rejudge"

    def get_context_data(self, **kwargs):
        context = super(RejudgeDone, self).get_context_data()
        submission_id = kwargs.get('submission_id')
        if submission_id:
            contest_submission = ContestSubmission.objects.get(
                id=submission_id)
            ensure_submission_contest_match(contest_submission, self.contest)
            context['contest_submission'] = contest_submission
        return context

class Teams(LoginRequiredMixin, ContestMixin, TemplateView):
    template_name = "contests/teams.html"
    title = "Teams"

    def get_context_data(self, **kwargs):
        context = super(Teams, self).get_context_data()
        context['teams'] = teams_with_member_list(self.contest)
        return context


class Leaderboard(UserPassesTestMixin, ContestMixin, TemplateView):
    template_name = 'contests/leaderboard.html'

    _stage = None

    title = "Leaderboard"

    @property
    def stage(self):
        if not self._stage:
            self._stage = ContestStage.objects.get(id=self.kwargs['stage_id'])
        return self._stage

    def test_func(self):
        return self.contest_context.can_see_stage_leaderboard(self.stage)

    def get_context_data(self, **kwargs):
        context = super(Leaderboard, self).get_context_data()
        if self.stage.contest != self.contest:
            raise SuspiciousOperation("Stage doesn't match contest")
        context['leaderboard'] = build_leaderboard(self.contest, self.stage)
        return context


class TeamCreate(UserPassesTestMixin, ContestMixin, CreateView):
    template_name='contests/new_team.html'
    model = Team
    fields = ['name']
    title = 'New Team'

    def test_func(self):
        return self.contest_context.can_create_team

    @transaction.atomic
    def form_valid(self, form):
        # TODO maybe move to model
        form.instance.contest = self.contest
        form.save()
        membership = TeamMember(
            team=form.instance,
            user=self.request.user,
            contest=self.contest
        )
        membership.save()
        return super(TeamCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('contests:team',
            args=[self.contest.code, self.object.id])


class JoinTeam(UserPassesTestMixin, ContestMixin, ContextMixin, View):
    _team = None

    @property
    def team(self):
        if not self._team:
            self._team = Team.objects.get(id=self.kwargs['team_id'])
        return self._team

    def test_func(self):
        return can_join_team(self.request.user, self.team)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        join_team_action(request.user, self.team)
        return redirect(
            reverse('contests:team', args=(self.contest.code, self.team.id)))


class LeaveTeam(UserPassesTestMixin, ContestMixin, ContextMixin, View):
    _team = None

    @property
    def team(self):
        if not self._team:
            self._team = Team.objects.get(id=self.kwargs['team_id'])
        return self._team

    def test_func(self):
        return self.contest_context.user_team == self.team

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        leave_team_action(request.user, self.team)
        return redirect(
            reverse('contests:team', args=(self.contest.code, self.team.id)))


class TeamView(LoginRequiredMixin, ContestMixin, TemplateView):
    template_name = 'contests/team.html'

    _team = None

    @property
    def team(self):
        if not self._team:
            return Team.objects.get(id=self.kwargs['team_id'])
        return self._team

    @property
    def title(self):
        return 'Team ' + self.team.name

    def get_context_data(self, **kwargs):
        context = super(TeamView, self).get_context_data()
        members = TeamMember.objects.select_related('user'). \
            filter(team=self.team).all()
        context['team'] = self.team
        context['members'] = members
        context['can_join'] = can_join_team(self.request.user, self.team)
        context['in_team'] = in_team(self.request.user, self.team)
        return context


class StartObserving(LoginRequiredMixin, ContestMixin, ContextMixin, View):

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        messages.add_message(request, messages.SUCCESS,
            mark_safe('You started observing contest <strong>%s</strong>.' %
                self.contest.name))
        self.contest.observing.add(request.user)
        return redirect(
            reverse('contests:description', args=(self.contest.code,)))


class StopObserving(LoginRequiredMixin, ContestMixin, ContextMixin, View):

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        self.contest.observing.remove(request.user)
        messages.add_message(request, messages.SUCCESS,
            mark_safe(
                'You are no longer observing contest <strong>%s</strong>.' %
                    self.contest.name))
        return redirect(
            reverse('contests:description', args=(self.contest.code,)))
