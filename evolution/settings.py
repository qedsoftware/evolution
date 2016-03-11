# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'base',
    'system',
    'contests'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    #'django_downloadview.SmartDownloadMiddleware'
)

ROOT_URLCONF = 'evolution.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'system.context_processors.system_settings',
                'system.context_processors.logo_link'
            ],
        },
    },
]

WSGI_APPLICATION = 'evolution.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'grading_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'grading_debug_log'),
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'base.management.commands.grading': {
            'handlers': ['console', 'grading_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'base.management.commands.grading_attempt_safe': {
            'handlers': ['console', 'grading_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'base.management.commands.grading_attempt': {
            'handlers': ['console', 'grading_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static_dir')]

# Grading

ATTEMPT_GRADING_COMMAND = [ os.path.join(BASE_DIR, './manage.py'),
    'grading_attempt' ]
RUNNER_PATH = os.path.join(BASE_DIR, 'run_scoring.py')

SCORING_TMP = '/tmp/evolution_scoring'

GRADING_POLL_FOR_JOB_INTERVAL_SECONDS=1
GRADING_CHECK_STATUS_INTERVAL_SECONDS=1

# Site

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login/'
LOGO_LINK_URL = 'http://qed.ai/'

# Downloads

DOWNLOADVIEW_BACKEND = 'django_downloadview.nginx.XAccelRedirectMiddleware'

#DOWNLOADVIEW_BACKEND = 'django_downloadview.nginx.XAccelRedirectMiddleware'

# Django Testing

TEST_RUNNER = 'evolution.runner.CustomTestSuiteRunner'

# we do it this way, so that local settings can read and change
# the parameters set here
local_settings_path = os.path.join(BASE_DIR, 'local_settings.py')
with open(local_settings_path) as local_file:
    exec(local_file.read(), globals())
