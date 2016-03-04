import datetime

from django.db import models
from django.db import transaction
from django.utils import timezone

from system.models import PostData, Post

from base.models import ScoringScript, DataGrader, Submission, \
    request_submission_grading, request_qs_grading

class Contest(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    description = models.ForeignKey('system.Post', related_name='+')
    rules = models.ForeignKey('system.Post', related_name='+')
    scoring_script = models.ForeignKey('base.ScoringScript')
    verification = models.ForeignKey('ContestStage', related_name='+',
        null=True)
    #test = models.ForeignKey('base.DataGrader', related_name='+')
    bigger_better = models.BooleanField(default=True)

class ContestFactory(object):
    """Creates and updates a contest, with all the related objects"""
    name = None
    code = None
    description = None
    scoring_script = None
    answer_for_verification = None

    @classmethod
    def from_dict(cls, data):
        factory = cls()
        factory.name = data.get('name')
        factory.code = data.get('code')
        factory.description = data.get('description')
        factory.rules = data.get('rules')
        factory.scoring_script = data.get('scoring_script')
        factory.answer_for_verification = data.get('answer_for_verification')
        factory.verification_begin = data.get('verification_begin')
        factory.verification_end = data.get('verification_end')
        return factory

    @transaction.atomic
    def create(self):
        description = Post()
        description.save()
        rules = Post()
        rules.save()
        scoring_script = ScoringScript()
        scoring_script.save()
        contest = Contest(name=self.name, code=self.code,
            description=description, rules=rules,
            scoring_script=scoring_script)
        contest.save()
        stage = ContestStage()
        stage.contest = contest
        stage.begin = timezone.now()
        stage.end = timezone.now()
        grader = DataGrader.create(scoring_script, None)
        grader.save()
        stage.grader = grader
        stage.save()
        contest.verification = stage
        contest.save()
        self.update(contest)
        return contest

    @transaction.atomic
    def update(self, contest):
        scoring_script = contest.scoring_script
        scoring_script.save_source(self.scoring_script)
        contest.name = self.name
        contest.code = self.code
        contest.description.from_data(self.description)
        contest.description.save()
        contest.rules.from_data(self.rules)
        contest.rules.save()
        contest.scoring_script.save_source(self.scoring_script)
        if self.verification_begin:
            contest.verification.begin = self.verification_begin
        if self.verification_end:
            contest.verification.end = self.verification_end
        contest.verification.grader.save_answer(self.answer_for_verification)
        contest.verification.grader.save()
        contest.verification.save()
        contest.save()

class ContestStage(models.Model):
    contest = models.ForeignKey('Contest', related_name='+')
    grader = models.ForeignKey('base.DataGrader', related_name='+')
    begin = models.DateTimeField()
    end = models.DateTimeField()

class Team(models.Model):
    name = models.CharField(max_length=100)
    contest = models.ForeignKey('Contest')

class TeamMember(models.Model):
    team = models.ForeignKey('Team', related_name='members')
    user = models.ForeignKey('auth.User', related_name='memberships')

class ContestSubmission(models.Model):
    stage = models.ForeignKey('ContestStage', related_name='+')
    submission = models.OneToOneField('base.Submission')
    #team = models.ForeignKey('Team')

class SubmissionData(object):
    output = None

@transaction.atomic
def submit(stage, submission_data):
    cs = ContestSubmission()
    cs.stage = stage
    submission = Submission.create(stage.grader, submission_data.output)
    request_submission_grading(submission)
    submission.save()
    cs.submission = submission
    cs.save()

def rejudge_submission(contest_submission):
    request_submission_grading(contest_submission.submission)
    contest_submission.submission.save()

def rejudge_contest(contest):
    request_qs_grading(Submission.objects.filter(contestsubmission__stage__contest=contest))
