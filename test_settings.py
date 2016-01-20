# -*- coding: utf-8 -*-
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
}


def run():
    from djangocms_helper import runner
    runner.cms('aldryn_reversion')

if __name__ == "__main__":
    run()
