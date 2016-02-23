import logging
import signal
import sys
import time

from django.conf import settings

from django.core.management.base import BaseCommand, CommandError

from base.utils import choose_for_grading, grade

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
            grade_attempt(attempt)
            time.sleep(settings.GRADING_INTERVAL_SECONDS)
