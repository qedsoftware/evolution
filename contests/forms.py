from django import forms
from django.core import validators

from .models import Contest
from system.models import PostData

class PostField(forms.Field):
    widget = forms.Textarea

    def to_python(self, value):
        if self.required and (value in validators.EMPTY_VALUES):
            return None
        # TODO allow formats other than markdown
        post_data = PostData.from_source(value, 'markdown')
        # maybe TODO, allow exceptions from build_html in the case
        # it doesn't parse
        post_data.build_html()
        return post_data

class ContestForm(forms.Form):
    name = forms.CharField(max_length=100)
    code = forms.SlugField(help_text="A short, unique name for a contest. It is used for urls and identifying contests. <strong>Avoid changing it.</strong> It can contain lowercase letters, numbers, hyphens and underscores.")
    description = PostField(required=False)
    rules = PostField(required=False)
    scoring_script = forms.FileField(required=False, help_text="Script used to score the results.")
    answer_for_verification = forms.FileField(required=False)
    #answer_test = forms.FileField()

class SubmitForm(forms.Form):
    output_file = forms.FileField()
