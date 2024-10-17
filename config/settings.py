# -*- coding: utf-8 -*-

"""
Django settings for django-photo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

import os
import sys
from django import urls

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEBUG = True

ALLOWED_HOSTS = ['localhost.photo', 'localhost']

ADMINS = (
    ('Alex Little', 'consult@alexlittle.net'),
)

SITE_ID = 1

ROOT_URLCONF = 'config.urls'

WSGI_APPLICATION = 'config.wsgi.application'


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'crispy_forms',
    'haystack',
    'celery',
    'celery_progress',
    'photo',
    'crispy_bootstrap4'
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


#####################################################################
# Templates

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
        },
    },
]

#####################################################################


#####################################################################
# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

#####################################################################


#####################################################################
# Static assets & media uploads
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'photo', 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
#####################################################################


#####################################################################
# Email
SERVER_EMAIL = 'Alex Little <consult@alexlittle.net>'
EMAIL_SUBJECT_PREFIX = '[Alex Little]: '
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_FILE_PATH = '/tmp/'
#####################################################################


#####################################################################
# Authentication
LOGIN_URL = urls.reverse_lazy('profile_login')
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
#####################################################################


#####################################################################
# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['console'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s',
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'photo': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}
#####################################################################

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': ''
        }
    }
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

######################################################################


# Celery Settings
BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

SESSION_COOKIE_NAME = "photo"

CRISPY_TEMPLATE_PACK = 'bootstrap4'
IGNORE_EXTENSIONS = []
IGNORE_FOLDERS = []
PHOTOS_PER_PAGE = 400
ALBUMS_PER_PAGE = 50

IMAGE_EXTENSIONS = ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.gif', '*.bmp', '*.JPG', '*.JPEG']


try:
    from config.local_settings import *
except ImportError:
    import warnings
    warnings.warn(
        "Using default settings."
        "Add `config/local_settings.py` for custom settings.")
