from django.db import models

from system.models import PostData, Post

class Contest(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    description = models.ForeignKey('system.Post')
    #verification = models.ForeignKey('base.DataGrader', related_name='+')
    #test = models.ForeignKey('base.DataGrader', related_name='+')

class ContestFactory(object):
    """Creates and updates a contest, with all the related objects"""
    name = None
    code = None
    description = None

    @classmethod
    def from_dict(cls, data):
        factory = cls()
        factory.name = data.get('name')
        factory.code = data.get('code')
        factory.description = data.get('description')
        return factory

    def create(self):
        post_data = PostData()
        post_data.source = self.description
        post_data.source_lang = 'markdown'
        post_data.build_html()
        post = Post()
        post.from_data(post_data)
        post.save()
        contest = Contest(name=self.name, code=self.code, description=post)
        contest.save()
        return contest

class ContestStage(models.Model):
    contest = models.ForeignKey('Contest', related_name='+')
    grader = models.ForeignKey('base.DataGrader', related_name='+')
    begin = models.DateTimeField()
    end = models.DateTimeField()

class ContestSubmission(models.Model):
    contest_stage = models.ForeignKey('ContestStage', related_name='+')
    submission = models.OneToOneField('base.Submission')
