################
Aldryn Reversion
################

|PyPI Version| |Build Status| |Coverage Status| |codeclimate| |requires_io|

***********
Description
***********

A collection of shared helpers and mixins to provide support for
django-reversion on models with translatable (using django-parler)
fields and/or django-cms placeholder fields.

Note: ::

    django-parler is optional and is not required. However, if your model is
    translated with Parler, aldryn-reversion will take translations and the
    resulting internal Parler translation cache into consideration when making
    revisions.


*****
Usage
*****

Please refer to  `documentation
<http://aldryn-reversions.readthedocs.org/en/latest/how_to/usage.html>`_. Or
`Aldryn Reversion documentation index
<http://aldryn-reversions.readthedocs.org>`_,


************
Requirements
************

* Python 2.6 or 2.7
* Django 1.6, 1.7 or 1.8
* django-reversion

Optional
========

* django CMS 3.0.12 or later
* django-parler


************
Installation
************

Most likely you don't need to install this addon by yourself, and it is
installed as a dependency for another addon.
If you do need to install this addon manually, just follow those steps:


1) Run `pip install aldryn-reversion`.

2) Add below apps to ``INSTALLED_APPS``: ::

    INSTALLED_APPS = [
        …
        'reversion',
        'aldryn_reversion',
        …
    ]

3) (Re-)Start your application server.


.. |PyPI Version| image:: http://img.shields.io/pypi/v/aldryn-reversion.svg
   :target: https://pypi.python.org/pypi/aldryn-reversion
.. |Build Status| image:: http://img.shields.io/travis/aldryn/aldryn-reversion/master.svg
   :target: https://travis-ci.org/aldryn/aldryn-reversion
.. |Coverage Status| image:: http://img.shields.io/coveralls/aldryn/aldryn-reversion/master.svg
   :target: https://coveralls.io/r/aldryn/aldryn-reversion?branch=master
.. |codeclimate| image:: https://codeclimate.com/github/aldryn/aldryn-reversion/badges/gpa.svg
   :target: https://codeclimate.com/github/aldryn/aldryn-reversion
   :alt: Code Climate
.. |requires_io| image:: https://requires.io/github/aldryn/aldryn-reversion/requirements.svg?branch=master
   :target: https://requires.io/github/aldryn/aldryn-reversion/requirements/?branch=master
   :alt: Requirements Status
