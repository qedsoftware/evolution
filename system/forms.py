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
    secret_code = forms.CharField(max_length=30, label="Secret Code")

    def signup(self, request, user):
        secret = self.cleaned_data.get('secret_code')
        invitation = Invitation.objects.filter(secret_code=secret).first()
        invitation.accepted = True
        invitation.save()
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

    def clean(self):
        cleaned_data = super(SignupForm, self).clean()
        secret = cleaned_data.get('secret_code').strip()
        cleaned_data['secret_code'] = secret # stripped
        invitation = Invitation.objects.filter(secret_code=secret).first()
        if not invitation:
            self.add_error('secret_code', 'Wrong Secret Code')
        if invitation.accepted:
            self.add_error('secret_code', 'Secret Code already used')
        if invitation.is_expired():
            self.add_error('secret_code', 'Invitation expired, maybe request a new one.')
        return cleaned_data
