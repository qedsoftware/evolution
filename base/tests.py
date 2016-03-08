import shutil
from pathlib import Path


from django.test import TestCase
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.conf import settings

from base.models import *
from base.models import _mkdir_scoring, _prepare_scoring_dir, \
    _run_scoring_popen


script_always_42 = """
print(42)
"""

data_2_and_2 = "2\n2\n"
data_3_and_3 = "3\n3\n"
data_3x3 = "3\n3\n3\n"


class GraderTest(TestCase):

    def test_create_grader(self):
        script = ScoringScript.create(ContentFile(script_always_42))
        grader = DataGrader.create(script, ContentFile(data_2_and_2))
        grader.save()
        grader.answer.url

    def test_simple_grader(self):
        grader = create_simple_grader(ContentFile(script_always_42),
            ContentFile(data_2_and_2))
        grader.save()

    def test_simple_grader_str(self):
        grader = create_simple_grader_str(script_always_42, data_2_and_2)
        grader.save()


class SubmissionTest(TestCase):
    def setUp(self):
        self.grader = create_simple_grader_str(script_always_42,
            data_2_and_2)

    def test_make_submission(self):
        submission = Submission.create(self.grader, ContentFile(data_2_and_2))
        submission.save()

    def test_choose_and_grade(self):
        submission = Submission.create(self.grader, ContentFile(data_2_and_2))
        request_submission_grading(submission)
        submission.save()
        submission.output.url
        sub, attempt = choose_for_grading()
        none1, none2 = choose_for_grading()
        self.assertIsNone(none1)
        self.assertIsNone(none2)
        dummy_grade(attempt)

    def test_single_grade(self):
        submission = Submission.create(self.grader, ContentFile(data_2_and_2))
        request_submission_grading(submission)
        submission.save()
        sub, attempt = choose_for_grading()
        call_command('grading_attempt', str(attempt.id))
        sub.refresh_from_db()
        attempt.refresh_from_db()
        self.assertTrue(attempt.finished)
        self.assertTrue(attempt.succed)
        self.assertEqual(attempt.score, 42)

class ScoringTest(TestCase):
    def setUp(self):
        self.grader = create_simple_grader_str(script_always_42,
            data_2_and_2)
        self.grader.save()
        self.submission = Submission.create(self.grader, ContentFile(data_2_and_2))
        request_submission_grading(self.submission)
        self.submission.save()
        _, self.attempt = choose_for_grading()
        self.assertIsNotNone(self.attempt)

    def test_mkdir_scoring(self):
        dir1 = _mkdir_scoring()
        # it should also create SCORING_TMP
        self.assertTrue(os.path.isdir(settings.SCORING_TMP))
        dir2 = _mkdir_scoring()
        dir3 = _mkdir_scoring()
        self.assertNotEqual(dir1, dir2)
        self.assertNotEqual(dir1, dir3)
        self.assertNotEqual(dir2, dir3)
        for directory in [dir1, dir2, dir3]:
            self.assertTrue(os.path.exists(directory))
            self.assertTrue(os.path.isdir(directory))
            self.assertTrue(os.path.isdir(directory))
            self.assertTrue(Path(settings.SCORING_TMP) in Path(dir1).parents)

    def test_prepare_scoring_dir(self):
        scoring_dir = _prepare_scoring_dir(self.attempt)
        # TODO more checks

    def test_run_scoring(self):
        scoring_dir = _prepare_scoring_dir(self.attempt)
        process = _run_scoring_popen(self.attempt, scoring_dir)
        process.wait()

    def test_attempt_grading(self):
        attempt_grading(self.attempt)
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.score, 42)
        self.assertEqual(self.attempt.finished, True)
        self.assertEqual(self.attempt.aborted, False)

    def test_attempt_aborted(self):
        self.attempt.aborted = True
        self.attempt.save()
        attempt_grading(self.attempt)
        self.attempt.refresh_from_db()
        self.assertIsNone(self.attempt.score)
        self.assertEqual(self.attempt.finished, False)
        self.assertEqual(self.attempt.aborted, True)

