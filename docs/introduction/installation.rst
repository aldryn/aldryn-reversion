############
Installation
############

Most likely you won't need to install this addon - it will be
installed as a dependency for some other addon.

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

You'll get the most benefit from aldryn-reversion if you're using it with django CMS and
django-parler. We'll assume you have a django CMS (version 3.x) project up and running.

If you need to set up a new django CMS project, follow the instructions
in the `django CMS tutorial
<http://docs.django-cms.org/en/develop/introduction/install.html>`_.

In this case ``django-parler`` should be installed as a dependency for
django CMS.


***************
``settings.py``
***************

Edit your ``INSTALLED_APPS`` to include the required applications::

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

.. todo:: say something about what these optional packages are

****************************
Prepare the database and run
****************************

Now run ``python manage.py migrate`` to prepare the database for the new
application, then ``python manage.py runserver``.

****************
For Aldryn users
****************

If you are using *any* addon that relies on ``aldryn-reversion`` it means
that you already have ``aldryn-reversion`` installed and configured.

If you are developing an Aldryn addon and want to use ``aldryn-reversion``
features in it, please refer to :doc:`configuration`
