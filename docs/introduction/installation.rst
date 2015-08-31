############
Installation
############

Most likely you don't need to install this addon by yourself, and it is
installed as a dependency for other addon.

*******************
Installing packages
*******************

Then run either::

    pip install aldryn-reversion

or to install from the latest source tree::

    pip install -e git+https://github.com/aldryn/aldryn-reversion.git#egg=aldryn-reversion


.. note::
   This should also install ``django-reversion`` (which is required) into your
   env.

To use aldryn-reversions at its full potential you might want to use it with
django CMS and django-parler. In that case we'll assume you have a
django CMS (version 3.x) project up and running.

If you need to set up a new django CMS project, follow the instructions
in the `django CMS tutorial
<http://docs.django-cms.org/en/develop/introduction/install.html>`_.

In this case ``django-parler`` should be installed as a dependency for
django CMS.


***********
settings.py
***********

Add below apps to ``INSTALLED_APPS``: ::

    INSTALLED_APPS = [
        …
        'reversion',
        'aldryn_reversion',
        …
    ]

.. note::
   ``reversion`` is required, but please check that it is included into
   ``INSTALLED_APPS`` only once, since it might be already there if you are
   using django CMS.

If you are planning to use the optional packages add them to
``INSTALLED_APPS`` too.

****************************
Prepare the database and run
****************************

Now run ``python manage.py migrate`` to prepare the database for the new
application, then ``python manage.py runserver``.

****************
For Aldryn users
****************

If you are using *ANY* addon that is relying on ``aldryn-reversion`` it means
that you already have ``aldryn-reversion`` installed and configured.

If you are developing an Aldryn addon and want to use ``aldryn-reversion``
features in it - please refer to :doc:`configuration`
