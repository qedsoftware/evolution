from django import forms

from .models import Contest

class ContestForm(forms.Form):
    name = forms.CharField(max_length=100)
    code = forms.SlugField(help_text="This is the grey text")
    description = forms.CharField(widget=forms.Textarea)
    #script_file = forms.FileField()
    #answer_verification = forms.FileField()
    #answer_test = forms.FileField()

class ContestForm2(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['code']
    #script_file = forms.FileField()
    #answer_verification = forms.FileField()
    #answer_test = forms.FileField()
