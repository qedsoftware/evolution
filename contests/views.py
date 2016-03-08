from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.views.generic.list import ListView
from django.views.generic.edit import FormView, CreateView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from system.views import title

from .models import Contest, ContestFactory, ContestSubmission, \
    SubmissionData, submit, ContestStage, rejudge_submission, \
    rejudge_contest, Team, TeamMember, join_team as join_team_action, \
    leave_team as leave_team_action, can_join_team, in_team, \
    is_contest_admin, teams_with_member_list, build_leaderboard, user_team

from .forms import ContestForm, ContestCreateForm, SubmitForm

from base.models import GradingAttempt

class ContestContext:
    """ Common data, required by all contest views. """
    is_contest_admin = None
    can_submit = None
    can_see_team_submissions = None
    can_see_all_submissions = None
    can_see_verification_leaderboard = None
    can_see_test_leaderboard = None
    user_team = None

    def __init__(self, request, contest):
        user = request.user
        if not user.is_authenticated():
            user = None
        self.user_team = user_team(user, contest)
        self.is_contest_admin = is_contest_admin(user, contest)
        self.can_see_team_submissions = self.user_team is not None
        self.can_see_all_submissions = self.is_contest_admin
        self.can_submit = self.user_team is not None or self.is_contest_admin
        self.can_see_verification_leaderboard = \
            contest.verification_stage.published_results
        self.can_see_test_leaderboard = \
            self.is_contest_admin or contest.test_stage.published_results

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

def contest_title(contest, text = None):
    return ' - '.join(filter(None, [contest.name, text]))


class ContestCreate(LoginRequiredMixin, FormView):
    form_class = ContestCreateForm
    template_name = "contests/contest_create_form.html"

    def form_valid(self, form):
        factory = ContestFactory.from_dict(form.cleaned_data)
        self.code = form.cleaned_data['code']
        contest = factory.create()
        contest.observing.add(self.request.user)
        return super(ContestCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('contests:setup', args=[self.code])

class ContestUpdate(LoginRequiredMixin, FormView):
    form_class = ContestForm
    template_name = "contests/contest_form.html"

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
        initial['published_final_leaderboard'] = \
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
        self.code = form.cleaned_data['code']
        contest = Contest.objects.get(code=self.get_code())
        factory.update(contest)
        contest.observing.add(self.request.user)
        contest.save()
        return super(ContestUpdate, self).form_valid(form)

    def get_success_url(self):
        return reverse('contests:setup', args=[self.code])


def description(request, contests_code=None):
    contest = Contest.objects.select_related('description'). \
        get(code=contests_code)
    return render(request, 'system/title_and_text.html', {
        'page_title': contest_title(contest, 'Description'),
        'content_title': 'Description',
        'text': contest.description.html,
        'contest': contest,
        'contest_context': ContestContext(request, contest)
    })

def rules(request, contests_code=None):
    contest = Contest.objects.select_related('rules'). \
        get(code=contests_code)
    return render(request, 'system/title_and_text.html', {
        'page_title': contest_title(contest, 'Rules'),
        'content_title': 'Rules',
        'text': contest.rules.html,
        'contest': contest,
        'contest_context': ContestContext(request, contest)
    })


class Submit(LoginRequiredMixin, FormView):
    form_class = SubmitForm
    template_name = "contests/submit_form.html"

    code = None

    def get_code(self):
        return self.kwargs['contests_code']

    def get_context_data(self, **kwargs):
        context = super(Submit, self).get_context_data()
        contest = Contest.objects.get(code=self.get_code())
        context['contest'] = contest
        context['contest_context'] = ContestContext(self.request, contest)
        return context

    def get_success_url(self):
        return reverse('contests:submissions',
            args=[self.get_code()])

    def get_stage(self, contest, form):
        stage_name = form.cleaned_data['stage']
        if stage_name == 'verification':
            return contest.verification_stage
        elif stage_name == 'test':
            return contest.test_stage

    def form_valid(self, form):
        data = SubmissionData()
        data.output = self.request.FILES['output_file']
        contest = Contest.objects.get(code=self.get_code())
        stage = self.get_stage(contest, form)
        submit(user_team(self.request.user, contest), stage, data)
        return super(Submit, self).form_valid(form)

class Submissions(LoginRequiredMixin, ListView):
    context_object_name = 'submissions'
    template_name = "contests/submissions.html"
    paginate_by = 10

    def get_queryset(self):
        return ContestSubmission.objects. \
            filter(stage__contest__code=self.kwargs['contests_code'])

    def get_context_data(self, **kwargs):
        context = super(Submissions, self).get_context_data()
        code = self.kwargs['contests_code']
        contest = Contest.objects.get(code=code)
        context['contest'] = contest
        context['contest_context'] = ContestContext(self.request, contest)
        return context

def ensure_submission_contest_match(submission, contest):
    if submission.stage.contest != contest:
        raise PermissionDenied()

@login_required
def submission(request, contests_code, submission_id):
    contest = Contest.objects.get(code=contests_code)
    contest_submission = ContestSubmission.objects. \
        select_related('submission').get(id=submission_id)
    submission = contest_submission.submission
    ensure_submission_contest_match(contest_submission, contest)
    grading_history = GradingAttempt.objects.filter(submission=submission). \
        order_by('-created_at').all()
    rejudge_url = reverse('contests:rejudge', args=[contest.code,
        contest_submission.id]) + '?next=' + request.path

    return render(request, 'contests/submission.html', {
        'contest': contest,
        'contest_context': ContestContext(request, contest),
        'contest_submission': contest_submission,
        'submission': submission,
        'grading_history': grading_history,
        'rejudge_url': rejudge_url
    })

@login_required
def rejudge_view(request, contests_code, submission_id=None):
    contest = Contest.objects.get(code=contests_code)
    if request.method == "POST":
        if submission_id:
            contest_submission = ContestSubmission.objects. \
                get(id=submission_id)
            ensure_submission_contest_match(contest_submission, contest)
            rejudge_submission(contest_submission)
            next = request.GET.get('next',
                default=reverse('contests:rejudge_done',
                    args=[contests_code, submission_id]))
        else:
            rejudge_contest(contest)
            next = request.GET.get('next',
                default=reverse('contests:rejudge_done',
                    args=[contests_code]))
        return redirect(next)
    else:
        if submission_id:
            return redirect(reverse('contests:submission',
                args=[contests_code, submission_id]))
        else:
            return render(request, 'contests/rejudge_all.html', {
                'contest': contest,
                'contest_context': ContestContext(request, contest)
            })

@login_required
def rejudge_done(request, contests_code, submission_id=None):
    contest = Contest.objects.get(code=contests_code)
    contest_submission = None
    if submission_id:
        contest_submission = ContestSubmission.objects.get(id=submission_id)
        ensure_submission_contest_match(contest_submission, contest)
    return render(request, 'contests/rejudge_done.html', {
        'contest': contest,
        'contest_context': ContestContext(request, contest),
        'contest_submission': contest_submission
    })

def teams(request, contests_code):
    contest = Contest.objects.get(code=contests_code)
    return render(request, 'contests/teams.html', {
        'contest': contest,
        'contest_context': ContestContext(request, contest),
        'teams': teams_with_member_list(contest)
    })

def leaderboard(request, contests_code, stage_id):
    contest = Contest.objects.get(code=contests_code)
    stage = ContestStage.objects.get(id=stage_id)
    if stage.contest != contest:
        raise SuspiciousOperation("Stage doesn't match contest")
    leaderboard = build_leaderboard(contest, stage)
    return render(request, 'contests/leaderboard.html', {
        'contest': contest,
        'contest_context': ContestContext(request, contest),
        'leaderboard': leaderboard
    })

class TeamCreate(CreateView):
    template_name='contests/new_team.html'
    model = Team
    fields = ['name']

    def get_code(self):
        return self.kwargs['contests_code']

    def get_context_data(self, **kwargs):
        context = super(TeamCreate, self).get_context_data()
        contest = Contest.objects.get(code=self.get_code())
        context['contest'] = contest
        context['contest_context'] = ContestContext(self.request, contest)
        return context

    def form_valid(self, form):
        contest = Contest.objects.get(code=self.get_code())
        form.instance.contest = contest
        form.save()
        return super(TeamCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('contests:team', args=[self.get_code(), self.object.id])

def join_team_view(request, contests_code, team_id):
    contest = Contest.objects.get(code=contests_code)
    team = Team.objects.get(id=team_id)
    join_team_action(request.user, team)
    return redirect(reverse('contests:team', args=(contests_code, team_id)))

def leave_team_view(request, contests_code, team_id):
    contest = Contest.objects.get(code=contests_code)
    team = Team.objects.get(id=team_id)
    leave_team_action(request.user, team)
    return redirect(reverse('contests:team', args=(contests_code, team_id)))

def team(request, contests_code, team_id):
    contest = Contest.objects.get(code=contests_code)
    team = Team.objects.get(id=team_id)
    members = TeamMember.objects.select_related('user').filter(team=team).all()
    return render(request, 'contests/team.html', {
        'contest': contest,
        'contest_context': ContestContext(request, contest),
        'team': team,
        'members': members,
        'can_join': can_join_team(request.user, team),
        'in_team': in_team(request.user, team)
    })
