from django import forms

from .models import Post, Invitation


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['source_lang', 'source']

    def save(self, commit=True):
        post = super(PostForm, self).save(commit=False)
        post_data = post.to_data()
        post_data.build_html()
        post.from_data(post_data)
        print('post_html:', post.html)
        if commit:
            post.save()
        return post


class InviteForm(forms.ModelForm):

    class Meta:
        model = Invitation
        fields = ['invited_email']


class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    secret_code = forms.CharField(max_length=30)

    def signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

    def clean(self):
        cleaned_data = super(SignupForm, self).clean()
        secret = cleaned_data.get('secret_code')
        if secret != '42':
            self.add_error('secret_code', 'Wrong Secret Code')
        return cleaned_data
