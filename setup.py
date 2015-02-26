# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from aldryn_reversion import __version__

REQUIREMENTS = [
    'django-cms>=3.0.9',
    'django-reversion>=1.8.2,<1.9',
]

CLASSIFIERS = [
    'Development Status :: 2 - Pre-Alpha',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
]

setup(
    name='aldryn-reversion',
    version=__version__,
    description='Support for django-reversion on models with translatable fields and django-cms placeholder fields.',
    author='Divio AG',
    author_email='info@divio.ch',
    url='https://github.com/aldryn/aldryn-reversion',
    packages=find_packages(),
    license='LICENSE.txt',
    platforms=['OS Independent', ],
    install_requires=REQUIREMENTS,
    classifiers=CLASSIFIERS,
    include_package_data=True,
    zip_safe=False,
    test_suite="test_settings.run",
    dependency_links=[
        'git+https://github.com/yakky/django-cms@future/integration#egg=django-cms-3.0.90a3',
        'django-reversion',
    ],
)
