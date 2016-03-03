import datetime

from django.db import models
from django.db import transaction

from system.models import PostData, Post

from base.models import ScoringScript, DataGrader

class Contest(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    description = models.ForeignKey('system.Post', related_name='+')
    rules = models.ForeignKey('system.Post', related_name='+')
    scoring_script = models.ForeignKey('base.ScoringScript')
    verification = models.ForeignKey('ContestStage', related_name='+',
        null=True)
    #test = models.ForeignKey('base.DataGrader', related_name='+')

class ContestFactory(object):
    """Creates and updates a contest, with all the related objects"""
    name = None
    code = None
    description = None
    scoring_script = None

    @classmethod
    def from_dict(cls, data):
        factory = cls()
        factory.name = data.get('name')
        factory.code = data.get('code')
        factory.description = data.get('description')
        factory.rules = data.get('rules')
        factory.scoring_script = data.get('scoring_script')
        factory.answer_for_verification = data.get('answer_for_verification')
        return factory

    @transaction.atomic
    def create(self):
        description = Post.new_from_data(self.description)
        rules = Post.new_from_data(self.rules)
        scoring_script = ScoringScript()
        scoring_script.source = self.scoring_script
        scoring_script.save()
        contest = Contest(name=self.name, code=self.code,
            description=description, rules=rules,
            scoring_script=scoring_script)
        contest.save()
        stage = ContestStage()
        stage.contest = contest
        stage.begin = datetime.datetime.now() # TODO
        stage.end = datetime.datetime.now() # TODO
        grader = DataGrader.create(scoring_script,
            self.answer_for_verification)
        grader.save()
        stage.grader = grader
        stage.save()
        contest.verification = stage
        contest.save()
        return contest

class ContestStage(models.Model):
    contest = models.ForeignKey('Contest', related_name='+')
    grader = models.ForeignKey('base.DataGrader', related_name='+')
    begin = models.DateTimeField()
    end = models.DateTimeField()

class Team(models.Model):
    name = models.CharField(max_length=100)

class TeamMember(models.Model):
    team = models.ForeignKey('Team', related_name='members')
    user = models.ForeignKey('auth.User', related_name='memberships')

class ContestSubmission(models.Model):
    contest_stage = models.ForeignKey('ContestStage', related_name='+')
    submission = models.OneToOneField('base.Submission')
    #team = models.ForeignKey('Team')

class SubmissionData(object):
    output = None

def submit(stage, submission_data):
    pass
