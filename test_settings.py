# -*- coding: utf-8 -*-

HELPER_SETTINGS = {
    'INSTALLED_APPS': [
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


def run():
    from djangocms_helper import runner
    runner.cms('aldryn_reversion')

if __name__ == "__main__":
    run()
