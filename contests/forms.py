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

CONTEST_CODE_HELP_TEXT = "A short, unique name for a contest. It is used for urls and identifying contests. <strong>Choose it carefully and avoid changing it.</strong> It can contain lowercase letters, numbers, hyphens and underscores."

class ContestCreateForm(forms.Form):
    error_css_class = 'input-error'

    name = forms.CharField(max_length=100)
    code = forms.SlugField(help_text=CONTEST_CODE_HELP_TEXT)

class ContestForm(forms.Form):
    error_css_class = 'input-error'

    name = forms.CharField(max_length=100)
    code = forms.SlugField(help_text=CONTEST_CODE_HELP_TEXT)
    description = PostField(required=False)
    rules = PostField(required=False)
    scoring_script = forms.FileField(required=False,
        help_text="A script used to score the results.",
        widget=ClearableFileInput())
    bigger_better = forms.BooleanField(
        label="The bigger the better",
        help_text="Are the bigger scores better (uncheck if smaller scores "
            "are better).", required=False)
    answer_for_verification = forms.FileField(required=False,
        widget=ClearableFileInput())
    verification_begin = forms.DateTimeField(required=False)
    verification_end = forms.DateTimeField(required=False)
    answer_for_test = forms.FileField(required=False,
        widget=ClearableFileInput())
    test_begin = forms.DateTimeField(required=False)
    test_end = forms.DateTimeField(required=False)
    published_final_results = forms.BooleanField(required=False)
    test_selected_limit = forms.IntegerField(required=False,
        help_text="Number of submissions users can choose to count in the "
            "leaderboard in the test stage. Avoid changing this value once the"
            "test stage starts — contestants will need to adjust.")

class SubmitForm(forms.Form):
    stage = forms.ChoiceField(choices=()) # we'll fill choices in __init__
    output_file = forms.FileField()
    source_code = forms.FileField()
    comment = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        stages_available = kwargs.pop('stages_available')
        self.base_fields['stage'].choices = stages_available
        super(SubmitForm, self).__init__(*args, **kwargs)
