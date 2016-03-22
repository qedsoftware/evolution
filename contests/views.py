from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic.base import ContextMixin, TemplateView, \
    View
from django.views.generic.list import ListView
from django.views.generic.edit import FormView, CreateView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.contrib import messages
from django.utils.safestring import mark_safe
from django_downloadview import BaseDownloadView

from .models import Contest, ContestFactory, ContestSubmission, \
    SubmissionData, submit, ContestStage, rejudge_submission, \
    rejudge_contest, Team, TeamMember, join_team as join_team_action, \
    leave_team as leave_team_action, can_join_team, in_team, \
    is_contest_admin, teams_with_member_list, build_leaderboard, user_team, \
    can_create_team, StageIsClosed, SelectionError, select_submission, \
    unselect_submission, remaining_selections

from .forms import ContestForm, ContestCreateForm, SubmitForm

from base.models import GradingAttempt
from system.views import PostDataView, add_static_message
from system.utils import calculate_once


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
    stage_names = None

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
        # we want user to be a model - so we can query easier
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
        self.is_observing = self.user and \
            contest.observing.filter(id=self.user.id).exists()
        self.stage_names = {
            contest.verification_stage.id: 'Verification',
            contest.test_stage.id: 'Final'
        }
        self.stages = [contest.verification_stage, contest.test_stage]

    def can_submit_in_stage(self, stage):
        return self.can_submit and (self.is_contest_admin or stage.is_open())

    def can_see_submission(self, submission):
        return is_contest_admin(self.user, self.contest) or \
            (submission.team is not None and submission.team == self.user_team)

    def can_see_stage_leaderboard(self, stage):
        return self.is_contest_admin or stage.published_results

    def visible_submission_result(self, submission):
        status = submission.submission.scoring_status
        if status is None:
            return 'waiting'
        if status == 'accepted':
            if self.is_contest_admin or submission.stage.published_results:
                return 'score'
            else:
                return 'accepted'
        else:
            return status

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


def add_contest_messages(context, contest_context):
    cc = contest_context
    if cc.user_team is None and not cc.is_contest_admin:
        add_static_message(context, messages.INFO,
            "To participate in the contest, join a team"
            " or create your own.")


def contest_title(contest, text=None):
    return ' - '.join(filter(None, [contest.name, text]))


class ContestMixin(object):
    """
    Common logic for views within a Contest

    Uses:
        contest_related - iterable of fields that will be
            select_related for contest
    """

    base_contest_related = [
        'test_stage',
        'verification_stage',
        'test_stage__contest',
        'verification_stage__contest'
    ]
    contest_related = []

    title = None

    @property
    def contest_code(self):
        return self.kwargs['contests_code']

    @calculate_once
    def contest_context(self):
        return ContestContext(self.request, self.contest)

    @calculate_once
    def contest(self):
        contest_qs = Contest.objects.filter(code=self.contest_code)
        for related in self.base_contest_related + self.contest_related:
            contest_qs = contest_qs.select_related(related)
        return contest_qs.get()

    @property
    def contest_url(self):
        return reverse('contests:description', args=(self.contest.code,))

    def get_context_data(self, **kwargs):
        context = super(ContestMixin, self).get_context_data(**kwargs)
        context['contest'] = self.contest
        context['contest_context'] = self.contest_context
        context['title'] = contest_title(self.contest, self.title)
        add_contest_messages(context, self.contest_context)
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
        contests = paginator.page(page)
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

    def get_context_data(self, **kwargs):
        context = super(ContestCreate, self).get_context_data(**kwargs)
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
        initial['selected_limit'] = contest.test_stage.selected_limit
        return initial

    def get_context_data(self, **kwargs):
        context = super(ContestUpdate, self).get_context_data(**kwargs)
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
    template_name = "contests/title_and_text.html"
    title = "Description"

    def get_context_data(self, **kwargs):
        context = super(Description, self).get_context_data(**kwargs)
        context['content_title'] = 'Description'
        context['text'] = self.contest.description.html
        return context


class Rules(LoginRequiredMixin, ContestMixin, TemplateView):
    template_name = "contests/title_and_text.html"
    title = "Rules"

    def get_context_data(self, **kwargs):
        context = super(Rules, self).get_context_data(**kwargs)
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
        return reverse('contests:my_submissions',
            args=[self.contest.code])

    def get_stage(self, form):
        stage_id = form.cleaned_data['stage']
        stage = ContestStage.objects.get(id=stage_id)
        if stage.contest != self.contest:
            raise PermissionDenied()
        return stage

    @calculate_once
    def stage_choices(self):
        choices = []
        for stage in self.contest_context.stages:
            if self.contest_context.can_submit_in_stage(stage):
                choices.append(
                    (stage.id, self.contest_context.stage_names[stage.id])
                )
        return choices

    def get_form_kwargs(self):
        kwargs = super(Submit, self).get_form_kwargs()
        choices = self.stage_choices
        kwargs['stages_available'] = choices
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(Submit, self).get_context_data(**kwargs)
        if not self.stage_choices:
            add_static_message(context, messages.WARNING,
                "Currently no stage is open for submissions.")
        return context

    def form_valid(self, form):
        data = SubmissionData()
        data.output = self.request.FILES['output_file']
        data.source = self.request.FILES['source_code']
        data.comment = form.cleaned_data['comment']
        stage = self.get_stage(form)
        # TODO move to model
        team = self.contest_context.user_team
        if team is None and not self.contest_context.is_contest_admin:
            raise PermissionDenied()
        try:
            submit(team, stage, data)
        except StageIsClosed:
            raise PermissionDenied()  # TODO be nicer
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
            select_related('submission'). \
            filter(stage__contest=self.contest). \
            order_by('-submission__created_at')


class MySubmissions(UserPassesTestMixin, ContestMixin, ListView):
    context_object_name = 'submissions'
    template_name = "contests/submissions.html"
    paginate_by = 10
    title = "My Submissions"

    def test_func(self):
        return self.contest_context.is_contest_admin or \
            self.contest_context.user_team is not None

    def get_queryset(self):
        # Filtering by team is not enough for technical (team=None) submissions
        return ContestSubmission.objects. \
            select_related('submission'). \
            filter(team=self.contest_context.user_team). \
            filter(stage__contest=self.contest). \
            order_by('-submission__created_at')


def ensure_submission_contest_match(submission, contest):
    if submission.stage.contest != contest:
        raise PermissionDenied()


class SubmissionMixin(ContestMixin):
    @calculate_once
    def submission(self):
        submission = ContestSubmission.objects. \
            select_related('submission'). \
            select_related('stage'). \
            get(id=self.kwargs['submission_id'])
        ensure_submission_contest_match(submission, self.contest)
        return submission

    @property
    def selection_change_active(self):
        """
        If the user can change the selection. This shouldn't take
        into account the number of selected submissions. Only the matters
        specific to this submission and stage.
        """
        # Maybe move to model?
        return self.submission.stage.requires_selection and \
            self.submission.stage.is_open() and \
            self.submission.team is not None and \
            self.contest_context.user_team == self.submission.team

    def get_context_data(self, **kwargs):
        context = super(SubmissionMixin, self).get_context_data(**kwargs)
        context['contest_submission'] = self.submission
        context['submission'] = self.submission.submission
        context['selection_change_active'] = self.selection_change_active
        return context


class SubmissionView(UserPassesTestMixin, SubmissionMixin, TemplateView):

    template_name = 'contests/submission.html'

    @property
    def title(self):
        return "Submission " + str(self.submission.id)

    def test_func(self):
        return self.contest_context.can_see_submission(self.submission)

    def rejudge_url(self):
        return reverse('contests:rejudge',
            args=[self.contest.code, self.submission.id]) + \
            '?next=' + self.request.path

    def get_context_data(self, **kwargs):
        context = super(SubmissionView, self).get_context_data(**kwargs)
        cs = self.submission
        submission = self.submission.submission
        grading_history = GradingAttempt.objects. \
            filter(submission=submission).order_by('-created_at').all()
        context['result'] = self.contest_context.visible_submission_result(cs)
        context['grading_history'] = grading_history
        context['rejudge_url'] = self.rejudge_url()
        context['stage_name'] = \
            self.contest_context.stage_names[self.submission.stage.id]
        context['remaining_selections'] = \
            remaining_selections(self.submission.team, self.submission.stage)
        return context


class DownloadSubmissionAnswer(UserPassesTestMixin, SubmissionMixin,
                               BaseDownloadView):
    def test_func(self):
        return self.contest_context.can_see_submission(self.submission)

    def get_file(self):
        return self.submission.submission.output


class DownloadSubmissionSource(UserPassesTestMixin, SubmissionMixin,
                               BaseDownloadView):
    def test_func(self):
        return self.contest_context.can_see_submission(self.submission)

    def get_file(self):
        return self.submission.source


class ContestRejudgeView(UserPassesTestMixin, ContestMixin, TemplateView):
    template_name = 'contests/rejudge_all.html'
    title = "Rejudge"

    rejudge_all_msg = "All submissions in the contest <strong>%s</strong> " \
        "were successfully marked for rejudging."

    def test_func(self):
        return self.contest_context.is_contest_admin

    def post(self, request, *args, **kwargs):
        rejudge_contest(self.contest)
        messages.add_message(self.request, messages.SUCCESS,
            mark_safe(self.rejudge_all_msg % self.contest.name))
        return redirect(request.GET.get('next', default=self.contest_url))


class SubmissionRejudgeView(UserPassesTestMixin, SubmissionMixin, ContextMixin,
                            View):
    rejudge_single_msg = "Submission <strong>%s</strong> was successfully " \
        "marked for rejudging."

    def test_func(self):
        return self.contest_context.is_contest_admin

    def post(self, request, *args, **kwargs):
        rejudge_submission(self.submission)
        messages.add_message(self.request, messages.SUCCESS, mark_safe(
            self.rejudge_single_msg % self.submission.id))
        return redirect(request.GET.get('next', default=self.contest_url))


class Leaderboard(UserPassesTestMixin, ContestMixin, TemplateView):
    template_name = 'contests/leaderboard.html'

    def test_func(self):
        return self.contest_context.can_see_stage_leaderboard(self.stage)

    def get_context_data(self, **kwargs):
        context = super(Leaderboard, self).get_context_data(**kwargs)
        if self.stage.contest != self.contest:
            raise SuspiciousOperation("Stage doesn't match contest")
        context['leaderboard'] = build_leaderboard(self.contest, self.stage)
        return context


class PublicLeaderboard(Leaderboard):
    template_name = 'contests/public_leaderboard.html'

    title = "Public Leaderboard"

    @property
    def stage(self):
        return self.contest.verification_stage


class TestLeaderboard(Leaderboard):
    template_name = 'contests/test_leaderboard.html'

    title = "Final Leaderboard"

    @property
    def stage(self):
        return self.contest.test_stage


class Teams(LoginRequiredMixin, ContestMixin, TemplateView):
    template_name = "contests/teams.html"
    title = "Teams"

    def get_context_data(self, **kwargs):
        context = super(Teams, self).get_context_data(**kwargs)
        context['teams'] = teams_with_member_list(self.contest)
        return context


class TeamCreate(UserPassesTestMixin, ContestMixin, CreateView):
    template_name = 'contests/new_team.html'
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

    @calculate_once
    def team(self):
        return Team.objects.get(id=self.kwargs['team_id'])

    def test_func(self):
        return can_join_team(self.request.user, self.team)

    def post(self, request, *args, **kwargs):
        join_team_action(request.user, self.team)
        return redirect(
            reverse('contests:team', args=(self.contest.code, self.team.id)))


class LeaveTeam(UserPassesTestMixin, ContestMixin, ContextMixin, View):

    @calculate_once
    def team(self):
        return Team.objects.get(id=self.kwargs['team_id'])

    def test_func(self):
        return self.contest_context.user_team == self.team

    def post(self, request, *args, **kwargs):
        leave_team_action(request.user, self.team)
        return redirect(
            reverse('contests:team', args=(self.contest.code, self.team.id)))


class TeamView(LoginRequiredMixin, ContestMixin, TemplateView):
    template_name = 'contests/team.html'

    @calculate_once
    def team(self):
        return Team.objects.get(id=self.kwargs['team_id'])

    @property
    def title(self):
        return 'Team ' + self.team.name

    def get_context_data(self, **kwargs):
        context = super(TeamView, self).get_context_data(**kwargs)
        members = TeamMember.objects.select_related('user'). \
            filter(team=self.team).all()
        context['team'] = self.team
        context['members'] = members
        context['can_join'] = can_join_team(self.request.user, self.team)
        context['in_team'] = in_team(self.request.user, self.team)
        return context


class StartObserving(LoginRequiredMixin, ContestMixin, ContextMixin, View):

    def post(self, request, *args, **kwargs):
        self.contest.observing.add(request.user)
        messages.add_message(request, messages.SUCCESS,
            mark_safe('You started observing contest <strong>%s</strong>.' %
                self.contest.name))
        return redirect(self.contest_url)


class StopObserving(LoginRequiredMixin, ContestMixin, ContextMixin, View):

    def post(self, request, *args, **kwargs):
        self.contest.observing.remove(request.user)
        messages.add_message(request, messages.SUCCESS,
            mark_safe('You are no longer observing contest'
                      ' <strong>%s</strong>.' % self.contest.name))
        return redirect(self.contest_url)


class SelectSubmission(UserPassesTestMixin, SubmissionMixin, ContextMixin,
                       View):

    def test_func(self):
        return self.contest_context.user_team == self.submission.team

    def post(self, request, *args, **kwargs):
        try:
            select_submission(self.submission)
            # it seems to much, they will notice
            # messages.add_message(request, messages.SUCCESS,
            #    mark_safe("Submission <strong>%s</strong> selected." %
            #        self.submission.id))
        except SelectionError as e:
            messages.error(request,
               mark_safe("<p>You failed to select submission"
                         " <strong>%s</strong>.</p>"
                         "<p>%s</p>" % (self.submission.id, str(e))))
        return redirect(
            reverse('contests:submission',
                args=(self.contest.code, self.submission.id)))


class UnselectSubmission(UserPassesTestMixin, SubmissionMixin, ContextMixin,
                         View):

    def test_func(self):
        return self.contest_context.user_team == self.submission.team

    def post(self, request, *args, **kwargs):
        try:
            unselect_submission(self.submission)
        except SelectionError as e:
            messages.error(request,
                mark_safe("<p>You failed to unselect submission"
                          " <strong>%s</strong>.</p>"
                          "<p>%s</p>" % (self.submission.id, str(e))))
        return redirect(
            reverse('contests:submission',
                args=(self.contest.code, self.submission.id)))


class ContestAdminHints(UserPassesTestMixin, PostDataView):
    post_template_name = "contests/hints_for_contest_admins.md"
    source_lang = 'markdown'
    content_title = "Hints for Contest Admins"

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super(ContestAdminHints, self).get_context_data(**kwargs)
        context['content_title'] = self.content_title
        return context
