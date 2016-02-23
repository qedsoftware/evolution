from django.db import models
from django.core.files.base import ContentFile
from django.db.models.functions import Now

def score_field(**kwargs):
    return models.DecimalField(max_digits=30, decimal_places=6, **kwargs)


class ScoringScript(models.Model):
    source = models.FileField()

    @classmethod
    def create(cls, source):
        script = cls()
        script.source.save('script', source)
        return script


class DataGrader(models.Model):
    scoring_script = models.ForeignKey('ScoringScript',
        on_delete=models.PROTECT)
    answer = models.FileField(null = True)

    @classmethod
    def create(cls, scoring_script, answer):
        grader = cls()
        grader.scoring_script = scoring_script
        grader.answer.save('grader_answer', answer)
        return grader


def create_simple_grader(script_file, answer_file):
    script = ScoringScript.create(script_file)
    grader = DataGrader.create(script, answer_file)
    return grader

def create_simple_grader_str(script_source, answer_data):
    return create_simple_grader(ContentFile(script_source),
        ContentFile(answer_data))


class Submission(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    grader = models.ForeignKey('DataGrader')
    answer = models.FileField(null=True)
    current_attempt = models.ForeignKey('GradingAttempt',
        on_delete=models.PROTECT, null=True, related_name='+')
    needs_grading = models.BooleanField(default=False)
    needs_grading_at = models.DateTimeField(null=True)
    score = score_field(null=True)

    @classmethod
    def create(cls, grader, answer):
        submission = cls(grader=grader, answer=answer)
        return submission


class GradingAttempt(models.Model):
    submission = models.ForeignKey('Submission', on_delete=models.PROTECT)
    finished = models.BooleanField(default=False)
    succed = models.BooleanField(default=False)
    score = score_field(null=True)
    abort = models.BooleanField(default=False)


# TODO adapt to accept queryset
def request_submission_grading(submission):
    submission.needs_grading = True
    submission.needs_grading_at = Now()

def choose_for_grading():
    submissions = Submission.objects.filter(needs_grading=True). \
        order_by('needs_grading_at')[:1]
    if not submissions.exists():
        return (None, None)
    submission = submissions[0]
    attempt = GradingAttempt(submission=submission)
    submission.attempt = attempt
    submission.needs_grading = False
    submission.save()
    attempt.save()
    return (submission, attempt)

def dummy_grade(attempt):
    attempt.score=1337
    attempt.submission.score = attempt.score
    attempt.finished = True
    attempt.succed = True
    attempt.submission.save()
    attempt.save()
