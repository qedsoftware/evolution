from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.views.generic.list import ListView
from django.views.generic.edit import FormView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from system.views import title

from .models import Contest, ContestFactory, ContestSubmission, \
    SubmissionData, submit, ContestStage
from .forms import ContestForm, SubmitForm

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

class ContestCreate(FormView):
    model = Contest
    form_class = ContestForm
    template_name = "contests/contest_form.html"

    def form_valid(self, form):
        factory = ContestFactory.from_dict(form.cleaned_data)
        factory.scoring_script = self.request.FILES.get('script_file')
        factory.answer_for_verification = \
            self.request.FILES.get('answer_for_verification')
        self.code = form.cleaned_data['code']
        factory.create()
        return super(ContestCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('contests:description', args=[self.code])

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

