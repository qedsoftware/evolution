from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.views.generic.list import ListView
from django.views.generic.edit import FormView, CreateView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import PermissionDenied

from django.contrib.auth.mixins import LoginRequiredMixin

from system.views import title

from .models import Contest, ContestFactory, ContestSubmission, \
    SubmissionData, submit, ContestStage, rejudge_submission, \
    rejudge_contest, Team, TeamMember
from .forms import ContestForm, SubmitForm

from base.models import GradingAttempt

def list(request):
    # Not a ListView because there will be more, user active contests etc.

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

    return render(request, 'contests/list.html', {'contests': contests})

def contest_title(contest, text = None):
    return ' - '.join(filter(None, [contest.name, text]))


class ContestCreate(LoginRequiredMixin, FormView):
    form_class = ContestForm
    template_name = "contests/contest_form.html"

    def form_valid(self, form):
        factory = ContestFactory.from_dict(form.cleaned_data)
        factory.scoring_script = self.request.FILES.get('scoring_script')
        factory.answer_for_verification = \
            self.request.FILES.get('answer_for_verification')
        self.code = form.cleaned_data['code']
        factory.create()
        return super(ContestCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('contests:description', args=[self.code])

class ContestUpdate(FormView):
    form_class = ContestForm
    template_name = "contests/contest_form.html"

    def get_code(self):
        return self.kwargs['contests_code']

    def get_initial(self):
        initial = super(ContestUpdate, self).get_initial()
        contest = Contest.objects. \
            select_related('description'). \
            select_related('rules'). \
            select_related('verification'). \
            get(code=self.get_code())
        initial['name'] = contest.name
        initial['code'] = contest.code
        initial['description'] = contest.description.source
        initial['rules'] = contest.rules.source
        initial['scoring_script'] = contest.scoring_script.source
        initial['answer_for_verification'] = contest.verification.grader.answer
        initial['verification_begin'] = contest.verification.begin
        initial['verification_end'] = contest.verification.end
        return initial

    def get_context_data(self, **kwargs):
        context = super(ContestUpdate, self).get_context_data()
        contest = Contest.objects.get(code=self.get_code())
        context['contest'] = contest
        context['content_title'] = 'Contest Settings'
        return context

    def form_valid(self, form):
        print(form.cleaned_data)
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
        'contest': contest
    })

def rules(request, contests_code=None):
    contest = Contest.objects.select_related('rules'). \
        get(code=contests_code)
    return render(request, 'system/title_and_text.html', {
        'page_title': contest_title(contest, 'Rules'),
        'content_title': 'Rules',
        'text': contest.rules.html,
        'contest': contest
    })


class Submit(FormView):
    form_class = SubmitForm
    template_name = "contests/submit_form.html"

    code = None

    def get_stage(self):
        contest = Contest.objects.select_related('verification'). \
            get(code=self.get_code())
        return contest.verification

    def get_code(self):
        return self.kwargs['contests_code']

    def get_context_data(self, **kwargs):
        context = super(Submit, self).get_context_data()
        contest = Contest.objects.get(code=self.get_code())
        context['contest'] = contest
        return context

    def get_success_url(self):
        return reverse('contests:submissions',
            args=[self.get_code()])

    def form_valid(self, form):
        data = SubmissionData()
        data.output = self.request.FILES['output_file']
        submit(self.get_stage(), data)
        return super(Submit, self).form_valid(form)


class ScoringData(View):
    def get(self, request):
        return render('contests/scoring_data.html')

class Submissions(ListView):
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
        return context

def ensure_submission_contest_match(submission, contest):
    if submission.stage.contest != contest:
        raise PermissionDenied()

def submission(request, contests_code, submission_id):
    contest = Contest.objects.get(code=contests_code)
    contest_submission = ContestSubmission.objects. \
        select_related('submission').get(id=submission_id)
    submission = contest_submission.submission
    ensure_submission_contest_match(contest_submission, contest)
    grading_history = GradingAttempt.objects.filter(submission=submission). \
        order_by('-created_at').all()
    return render(request, 'contests/submission.html', {
        'contest': contest,
        'contest_submission': contest_submission,
        'submission': submission,
        'grading_history': grading_history
    })

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
                'contest': contest })

def rejudge_done(request, contests_code, submission_id=None):
    contest = Contest.objects.get(code=contests_code)
    contest_submission = None
    if submission_id:
        contest_submission = ContestSubmission.objects.get(id=submission_id)
        ensure_submission_contest_match(contest_submission, contest)
    return render(request, 'contests/rejudge_done.html', {
        'contest': contest,
        'contest_submission': contest_submission
    })

class TeamList(ListView):
    template_name='contests/teams.html'

    paginate_by=10

    def get_code(self):
        return self.kwargs['contests_code']

    def get_queryset(self):
        return Team.objects.filter(contest__code=self.get_code())

    def get_context_data(self, **kwargs):
        context = super(TeamList, self).get_context_data()
        contest = Contest.objects.get(code=self.get_code())
        context['contest'] = contest
        return context

class CreateTeam(CreateView):
    pass

def join_team(request, contests_code, team_id):
    pass

def leave_team(request, contests_code, team_id):
    pass

def team(request, contests_code, team_id):
    pass
