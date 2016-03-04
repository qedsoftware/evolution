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

class ClearableFileInput(forms.ClearableFileInput):
    template_with_initial = (
        '<div class="upload-input-ctrl">'
        '<div class="upload-input-part"><span class=pseudo-label>%(initial_text)s:</span> <a href="%(initial_url)s">%(initial)s</a> </div>'
        '<div class="upload-input-part">%(clear_template)s</div>'
        '<div class="upload-input-part"><span class=pseudo-label>%(input_text)s:</span> %(input)s</div>'
        '</div>'
    )
    template_with_clear = '<label for="%(clear_checkbox_id)s">%(clear_checkbox_label)s:</label> %(clear)s'

class ContestForm(forms.Form):
    error_css_class = 'input-error'

    name = forms.CharField(max_length=100)
    code = forms.SlugField(help_text="A short, unique name for a contest. It is used for urls and identifying contests. <strong>Avoid changing it.</strong> It can contain lowercase letters, numbers, hyphens and underscores.")
    description = PostField(required=False)
    rules = PostField(required=False)
    scoring_script = forms.FileField(required=False,
        help_text="A script used to score the results.",
        widget=ClearableFileInput())
    bigger_better = forms.BooleanField(label="The bigger the better", help_text="Are the bigger scores better (uncheck if smaller scores are better).")
    answer_for_verification = forms.FileField(required=False,
        widget=ClearableFileInput())
    verification_begin = forms.DateTimeField(required=False)
    verification_end = forms.DateTimeField(required=False)
    #answer_test = forms.FileField()

class SubmitForm(forms.Form):
    output_file = forms.FileField()
