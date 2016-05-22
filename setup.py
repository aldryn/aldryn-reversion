# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from aldryn_reversion import __version__

REQUIREMENTS = [
    'Django>=1.6,<1.10',
    'django-cms>=3.0.12',
    'django-reversion>=1.8.2,<1.11',
]

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Framework :: Django :: 1.6',
    'Framework :: Django :: 1.7',
    'Framework :: Django :: 1.8',
    'Framework :: Django :: 1.9',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
]

setup(
    name='aldryn-reversion',
    version=__version__,
    description='Support for django-reversion on models with translatable '
                'fields and django-cms placeholder fields.',
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
)
