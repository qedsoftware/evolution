import shutil
import os
import tempfile
import json
import subprocess
from decimal import Decimal

from django.db import models, transaction
from django.core.files.base import ContentFile
from django.db.models.functions import Now
from django.conf import settings
from django.utils import timezone


class ScoringScript(models.Model):
    source = models.FileField(null=True, blank=True)

    @classmethod
    def create(cls, source):
        script = cls()
        script.save_source(source)
        return script

    def save_source(self, source):
        if source:
            self.source.save('script.py', source)
        elif source == False:
            self.source.delete()


DEFAULT_TIME_LIMIT = 1000

class DataGrader(models.Model):
    scoring_script = models.ForeignKey('ScoringScript',
        on_delete=models.PROTECT)
    answer = models.FileField(null = True, blank=True)
    time_limit_ms = models.IntegerField(default=DEFAULT_TIME_LIMIT)

    @classmethod
    def create(cls, scoring_script, answer, time_limit_ms=DEFAULT_TIME_LIMIT):
        grader = cls()
        grader.scoring_script = scoring_script
        grader.time_limit_ms = time_limit_ms
        grader.save_answer(answer)
        return grader

    def save_answer(self, answer):
        if answer:
            self.answer.save('grader_answer', answer)
        elif answer == False:
            self.answer.delete()


def create_simple_grader(script_file, answer_file,
                         time_limit_ms=DEFAULT_TIME_LIMIT):
    script = ScoringScript.create(script_file)
    grader = DataGrader.create(script, answer_file, time_limit_ms)
    return grader

def create_simple_grader_str(script_source, answer_data,
                             time_limit_ms=DEFAULT_TIME_LIMIT):
    return create_simple_grader(ContentFile(script_source),
        ContentFile(answer_data), time_limit_ms=time_limit_ms)

def score_field():
    return models.DecimalField(max_digits=30, decimal_places=6, null=True)

class Submission(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    grader = models.ForeignKey('DataGrader')
    output = models.FileField(null=True)
    current_attempt = models.ForeignKey('GradingAttempt',
        on_delete=models.PROTECT, blank=True, null=True, related_name='+')
    needs_grading = models.BooleanField(default=False)
    needs_grading_at = models.DateTimeField(null=True)
    score = score_field()

    @classmethod
    def create(cls, grader, output):
        submission = cls(grader=grader)
        if output:
            submission.output.save('output', output)
        submission.save()
        return submission


class GradingAttempt(models.Model):
    submission = models.ForeignKey('Submission', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    succed = models.BooleanField(default=False)
    score = score_field()
    aborted = models.BooleanField(default=False)
    log = models.FileField()

def request_submission_grading(submission):
    submission.needs_grading = True
    submission.needs_grading_at = Now()

def request_qs_grading(submissions):
    submissions.update(needs_grading=True, needs_grading_at=Now())

@transaction.atomic
def choose_for_grading():
    submissions = Submission.objects.filter(needs_grading=True). \
        order_by('needs_grading_at')[:1]
    if not submissions.exists():
        return (None, None)
    submission = submissions[0]
    attempt = GradingAttempt(submission=submission)
    attempt.save()
    submission.current_attempt = attempt
    submission.needs_grading = False
    submission.save()
    return (submission, attempt)

def dummy_grade(attempt):
    attempt.score = 42
    attempt.finished = True
    attempt.succed = True
    attempt.submission.save()
    attempt.save()

def _mkdir_scoring():
    os.makedirs(settings.SCORING_TMP, exist_ok=True)
    return tempfile.mkdtemp(prefix='scoring_', dir=settings.SCORING_TMP)

def _file_path(field_file):
    return field_file.path

def _prepare_scoring_dir(attempt):
    scoring_dir = _mkdir_scoring()
    output_path = os.path.join(scoring_dir, 'user_output')
    shutil.copyfile(_file_path(attempt.submission.output), output_path)
    answer_path = os.path.join(scoring_dir, 'answer')
    shutil.copyfile(_file_path(attempt.submission.grader.answer), answer_path)
    script_path = os.path.join(scoring_dir, 'scoring_script.py')
    shutil.copyfile(
        _file_path(attempt.submission.grader.scoring_script.source),
        script_path)
    attempt.log.save('scoring_log', ContentFile(''))
    log_file_path = _file_path(attempt.log)
    working_path = os.path.join(scoring_dir, 'working')
    config = {
        'working_directory': working_path,
        'scoring_script': script_path,
        'user_output': output_path,
        'answer': answer_path,
        'scoring_log': log_file_path,
        'time_limit_ms': attempt.submission.grader.time_limit_ms
    }
    config_path = os.path.join(scoring_dir, 'config.json')
    with open(config_path, 'w') as config_file:
        json.dump(config, config_file)
    return scoring_dir

def _run_scoring_popen(attempt, scoring_dir):
    args = [settings.RUNNER_PATH, scoring_dir]
    return subprocess.Popen(args, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

@transaction.atomic
def update_submission_score(attempt):
    # We dance a little to avoid races.
    # TODO check this more carefully
    submission = Submission.objects. \
        filter(current_attempt=attempt).select_for_update()
    if submission.exists():
        submission = submission.get()
        submission.score = attempt.score
        submission.save()

def attempt_grading(attempt):
    scoring_dir = _prepare_scoring_dir(attempt)
    process = _run_scoring_popen(attempt, scoring_dir)
    finished = False
    while not finished:
        attempt.refresh_from_db()
        if attempt.aborted:
            return
        try:
            # in theory this can deadlock if process generates ton of output
            # TODO: change to passing data through files
            # I am not sure if communicate is the right solution either
            process.wait(
                timeout=settings.GRADING_CHECK_STATUS_INTERVAL_SECONDS)
            finished = True
        except TimeoutExpired:
            pass
    attempt.finished = True
    attempt.finished_at = timezone.now()
    if process.returncode == 0:
        # we got the answer!
        # TODO handle precision explicitly
        # TODO parse more carefully (run_scoring should filter it already)
        output = process.stdout.read().decode('utf-8')
        attempt.score = Decimal(output)
        attempt.succed = True
    else:
        # TODO logging!
        attempt.succed = False
    # We don't want to overwrite abort
    attempt.save(update_fields=['succed', 'score', 'finished'])
    update_submission_score(attempt)
