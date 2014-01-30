"""
Bare-minimum django settings file
"""
from __future__ import unicode_literals, print_function

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'multires.sqlite'
    }
}

INSTALLED_APPS = (
    'south',
    'django_nose',
    'multires',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = (
    '--all-modules',
    '--with-doctest',
    '--with-coverage',
    '--cover-package=multires',
)

STATIC_URL = '/static/'
SECRET_KEY = 'foo'
