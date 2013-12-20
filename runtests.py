#!/usr/bin/env python
import django
from django.conf import settings, global_settings as default_settings
from django.core.management import call_command
import os.path
import sys
import os

# Give feedback on used versions
sys.stderr.write('Using Python version {0} from {1}\n'.format(sys.version[:5], sys.executable))
sys.stderr.write('Using Django version {0} from {1}\n'.format(
    django.get_version(),
    os.path.dirname(os.path.abspath(django.__file__)))
)

# Detect location and available modules
module_root = os.path.dirname(os.path.realpath(__file__))

# Inline settings file
settings.configure(
    DEBUG = False,  # will be False anyway by DjangoTestRunner.
    TEMPLATE_DEBUG = False,
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:'
        }
    },
    TEMPLATE_DIRS = (os.path.join(module_root, 'tests', 'templates'), ),
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader'
    ),
    TEMPLATE_CONTEXT_PROCESSORS = default_settings.TEMPLATE_CONTEXT_PROCESSORS + (
        'django.core.context_processors.request',
    ),
    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',

        'rest_framework',
        'polymorphic',

        'bulbs.content',
        'bulbs.images',
        'bulbs.indexable',

        'tests.testindexable'  # Just here for a couple of test models
    ),
    SITE_ID = 3,

    ROOT_URLCONF = 'tests.urls',
    
    ES_DISABLED = False,
    ES_URLS = ['http://localhost:9200'],
    ES_INDEXES = {
        'default': 'testing'
    },

    BETTY_CROPPER = {
            'ADMIN_URL': 'http://localhost:8698/',
            'PUBLIC_URL': 'http://localhost:8698/',
            'DEFAULT_IMAGE': '12345'
    }
)
if django.VERSION[1] < 6:
    settings.INSTALLED_APPS += ('discover_runner',)
    # settings.TEST_RUNNER = 'tests.runner.XMLTestRunner'
    settings.TEST_RUNNER = 'discover_runner.DiscoverRunner'
    settings.TEST_DISCOVER_TOP_LEVEL = os.path.join(module_root, 'bulbs')
    print(settings.TEST_DISCOVER_TOP_LEVEL)


call_command('syncdb', verbosity=1, interactive=False)

# ---- app start
verbosity = 2 if '-v' in sys.argv else 1

from django.test.utils import get_runner
TestRunner = get_runner(settings)  # DjangoTestSuiteRunner
runner = TestRunner(verbosity=verbosity, interactive=True, failfast=False)
failures = runner.run_tests(['bulbs',])

if failures:
    sys.exit(bool(failures))