import shutil
import tempfile

from django.conf import settings
from django.test.runner import DiscoverRunner


# Based on:
# https://www.caktusgroup.com/blog/2013/06/26/media-root-and-django-tests/
class TempMediaMixin(object):
    "Mixin to create MEDIA_ROOT in temp and tear down when complete."

    def setup_test_environment(self):
        "Create temp directory and update MEDIA_ROOT and default storage."
        super(TempMediaMixin, self).setup_test_environment()
        settings._original_media_root = settings.MEDIA_ROOT
        settings._original_scoring_tmp = settings.SCORING_TMP
        settings._original_file_storage = settings.DEFAULT_FILE_STORAGE
        self._temp_media = tempfile.mkdtemp()
        self._temp_scoring = tempfile.mkdtemp()
        settings.MEDIA_ROOT = self._temp_media
        settings.SCORING_TMP = self._temp_scoring
        settings.DEFAULT_FILE_STORAGE = \
            'django.core.files.storage.FileSystemStorage'

    def teardown_test_environment(self):
        "Delete temp storage."
        super(TempMediaMixin, self).teardown_test_environment()
        shutil.rmtree(self._temp_media, ignore_errors=True)
        shutil.rmtree(self._temp_scoring, ignore_errors=True)
        settings.MEDIA_ROOT = settings._original_media_root
        del settings._original_media_root
        settings.SCORING_TMP = settings._original_scoring_tmp
        del settings._original_scoring_tmp
        settings.DEFAULT_FILE_STORAGE = settings._original_file_storage
        del settings._original_file_storage


class CustomTestSuiteRunner(TempMediaMixin, DiscoverRunner):
    "Local test suite runner."
