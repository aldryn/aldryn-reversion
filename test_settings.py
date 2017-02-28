# -*- coding: utf-8 -*-
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os


PROJECT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'aldryn_reversion', 'test_helpers')
)


HELPER_SETTINGS = {
    'INSTALLED_APPS': [
        'djangocms_text_ckeditor',
        'parler',
        'reversion',
        'aldryn_reversion',
        'aldryn_reversion.test_helpers.project.test_app',
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
    'MIDDLEWARE_CLASSES': [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'cms.middleware.user.CurrentUserMiddleware',
        'cms.middleware.page.CurrentPageMiddleware',
        'cms.middleware.toolbar.ToolbarMiddleware',
        'cms.middleware.language.LanguageCookieMiddleware'
    ],
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
    'CMS_TEMPLATES': (
        ('simple.html', 'simple'),
    ),
    'TEMPLATE_DIRS': [
        os.path.abspath(os.path.join(PROJECT_PATH, 'project', 'templates'))],
    'TEMPLATES': [{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.abspath(os.path.join(PROJECT_PATH, 'project', 'templates'))],
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
                'django.core.context_processors.static',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'django.template.loaders.eggs.Loader',
            ],
        },
    }]
}


def run():
    from djangocms_helper import runner
    runner.cms('aldryn_reversion')

if __name__ == "__main__":
    run()
