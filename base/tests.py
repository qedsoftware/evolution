import shutil

from django.test import TestCase
from django.core.files.base import ContentFile
from django.core.management import call_command

from base.models import *

from django.conf import settings

script_abs_diff_sum = """
""";

data_2_and_2 = "2\n2\n"
data_3_and_3 = "3\n3\n"
data_3x3 = "3\n3\n3\n"

def clean_media():
    shutil.rmtree(settings.MEDIA_ROOT)

class GraderTest(TestCase):
    def tearDown(self):
        clean_media()

    def test_create_grader(self):
        script = ScoringScript.create(ContentFile(script_abs_diff_sum))
        grader = DataGrader.create(script, ContentFile(data_2_and_2))
        grader.save()

    def test_simple_grader(self):
        grader = create_simple_grader(ContentFile(script_abs_diff_sum),
            ContentFile(data_2_and_2))
        grader.save()

    def test_simple_grader_str(self):
        grader = create_simple_grader_str(script_abs_diff_sum, data_2_and_2)
        grader.save()


class SubmissionTest(TestCase):
    def setUp(self):
        self.grader = create_simple_grader_str(script_abs_diff_sum,
            data_2_and_2)

    def tearDown(self):
        clean_media()

    def test_make_submission(self):
        submission = Submission.create(self.grader, ContentFile(data_2_and_2))
        submission.save()

    def test_choose_and_grade(self):
        submission = Submission.create(self.grader, ContentFile(data_2_and_2))
        request_submission_grading(submission)
        submission.save()
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
        call_command('grade_attempt', attempt_id=attempt.id)
        sub.refresh_from_db()
        attempt.refresh_from_db()
        assert(attempt.finished)
        assert(attempt.succed)
        self.assertEqual(attempt.score, 1337)
        self.assertEqual(sub.score, 1337)

