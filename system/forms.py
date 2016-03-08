from django import forms

from .models import Post

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
