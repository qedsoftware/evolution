import logging
import signal
import sys
import time
import subprocess

from django.conf import settings

from django.core.management.base import BaseCommand, CommandError

from base.models import GradingAttempt, attempt_grading

logger = logging.getLogger(__name__)

def exit_on_signal(signum, frame):
    logger.info('grading_attempt_safe terminated by signal %s', signum)
    sys.exit(1)

class Command(BaseCommand):
    help = 'Runs grading of single attempt, allows aborting of tasks, ' \
        'guaranteed to finish peacefully if attempt_id is valid (internal).'

    def add_arguments(self, parser):
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
        logger.info('grading_attempt started')
        completed = subprocess.run(settings.ATTEMPT_GRADING_COMMAND +
            [str(attempt_id)])
        logger.info('grading_attempt finished (status_code = %s)' %
            completed.returncode)
