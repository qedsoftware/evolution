import logging
import signal
import sys
import time

from django.conf import settings

from django.core.management.base import BaseCommand
from django.core.management import call_command

from base.models import choose_for_grading

logger = logging.getLogger(__name__)


def exit_on_signal(signum, frame):
    logger.info('Grading terminated by signal %s', signum)
    sys.exit(1)


class Command(BaseCommand):
    help = 'Runs grading'

    def handle(self, *args, **options):
        signal.signal(signal.SIGINT, exit_on_signal)
        signal.signal(signal.SIGTERM, exit_on_signal)
        while True:
            submission, attempt = choose_for_grading()
            if submission is None:
                time.sleep(settings.GRADING_POLL_FOR_JOB_INTERVAL_SECONDS)
            else:
                logger.info('Grading submission %s, attempt %s', submission.id,
                    attempt.id)
                call_command('grading_attempt_safe', str(attempt.id))
