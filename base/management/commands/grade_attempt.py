import logging
import signal
import sys
import time

from django.conf import settings

from django.core.management.base import BaseCommand, CommandError

from base.models import GradingAttempt, dummy_grade

logger = logging.getLogger(__name__)

def exit_on_signal(signum, frame):
    logger.info('Grading terminated by signal %s', signum)
    sys.exit(1)

class Command(BaseCommand):
    help = 'Grades single attempt (internal)'

    def add_argument():
        parser.add_argument('attempt_id', type=int)

    def handle(self, *args, **options):
        signal.signal(signal.SIGINT, exit_on_signal)
        signal.signal(signal.SIGTERM, exit_on_signal)
        attempt_id = options['attempt_id']
        try:
            attempt = GradingAttempt.objects.get(id=attempt_id)
        except GradingAttempt.DoesNotExist:
            raise CommandError("GradingAttempt %s does not exist" %
                attempt_id)
        # Dummy grading
        time.sleep(1)
        dummy_grade(attempt)

