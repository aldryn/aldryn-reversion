# -*- coding: utf-8 -*-
from distutils.version import LooseVersion
from django import get_version

django_version = LooseVersion(get_version())

HELPER_SETTINGS = {
    'INSTALLED_APPS': [
        'djangocms_text_ckeditor',
        'parler',
        'reversion',
        'aldryn_reversion',
        'aldryn_reversion.test_helpers.test_app',
    ],
    # affects test cases with translations
    'PARLER_ENABLE_CACHING': False,
    'LANGUAGES': (
        ('en', 'English'),
        ('de', 'German'),
    ),
    'PARLER_LANGUAGES': {
        1: (
            {'code': 'en', },
            {'code': 'de', },
        ),
        'default': {
            'hide_untranslated': True,
        }
    },
    'CMS_LANGUAGES': {
        1: [
            {
                'code': 'de',
                'name': 'Deutsche',
                'fallbacks': ['en', ]
            },
            {
                'code': 'en',
                'name': 'English',
                'fallbacks': ['de', ]
            },
        ],
        'default': {
            'redirect_on_fallback': True,
        }
    },
}

if django_version >= LooseVersion('1.8.0'):
    HELPER_SETTINGS.update({
        'TEMPLATES': [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'OPTIONS': {
                    'context_processors': [
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                        'django.core.context_processors.i18n',
                        'django.core.context_processors.debug',
                        'django.core.context_processors.request',
                        'django.core.context_processors.media',
                        'django.core.context_processors.csrf',
                        'django.core.context_processors.tz',
                        'sekizai.context_processors.sekizai',
                        'django.core.context_processors.static',
                        'cms.context_processors.cms_settings',
                    ],
                    'loaders': [
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                    ],
                },
            },
        ]
    })


def run():
    from djangocms_helper import runner
    runner.cms('aldryn_reversion')

if __name__ == "__main__":
    run()
