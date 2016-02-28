from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.views.generic.edit import FormView

from system.views import title

from .models import Contest, ContestFactory
from .forms import ContestForm, ContestForm2


# Create your views here.
def list(request):
    return render(request, "contests/list.html", {})

def contest_title(contest, text = None):
    return ' - '.join(filter(None, [contest.name, text]))

class ContestCreate(FormView):
    model = Contest
    form_class = ContestForm
    template_name = "contests/contest_form.html"

    def form_valid(self, form):
        factory = ContestFactory.from_dict(form.cleaned_data)
        self.code = form.cleaned_data['code']
        factory.create()
        return super(ContestCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse(description, kwargs={'contest_code': self.code})

def description(request, contests_code=None):
    contest = Contest.objects.select_related('description'). \
        get(code=contests_code)
    return render(request, 'system/title_and_text.html', {
        'page_title': contest_title(contest, 'Description'),
        'content_title': 'Description',
        'text': contest.description.html,
        'contest': contest
    })
