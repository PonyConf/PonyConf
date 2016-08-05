# -*- coding: utf-8 -*-

import logging

from django.utils import six

from ponyconf.settings import *


DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS += (
    'debug_toolbar',
    'django_extensions',
)

INTERNAL_IPS = ('127.0.0.1',)  # Used by app debug_toolbar

EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

TIME_ZONE = 'Europe/Paris'
LANGUAGE_CODE = 'fr-FR'
