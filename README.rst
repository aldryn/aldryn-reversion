================
Aldryn Reversion
================

|PyPI Version| |Build Status| |Coverage Status| |codeclimate| |requires_io|

Description
~~~~~~~~~~~

Support for django-reversion on models with translatable (using django-parler)
fields and/or django-cms placeholder fields.

Note: ::

    django-parler is optional and is not required. However, if your model is
    translated with Parler, aldryn-reversion will take translations and the
    resulting internal Parler translation cache into consideration when making
    revisions.


--------------------
Installation & Usage
--------------------

Aldryn Platform Users
~~~~~~~~~~~~~~~~~~~~~

TODO


Manual Installation
~~~~~~~~~~~~~~~~~~~

1) Run `pip install aldryn-reversion`.

2) Add below apps to ``INSTALLED_APPS``: ::

    INSTALLED_APPS = [
        …
        'aldryn_reversion',
        …
    ]

3) (Re-)Start your application server.


Usage
~~~~~

Using Aldryn Reversion in your project is relatively simple.

There are two parts. Adding a registration decorator to your model and adding a
mixin to your admin class definition for the same model.

For the model, add ``version_controlled_content`` as a decorator like so: ::

    from aldryn-reversion.core import version_controlled_content

    @version_controlled_content
    class MyModel(models.Model):
        ...

If yor model has FK relations you can use `follow` property from
`django-reversions` when applying decorator: ::

    @version_controlled_content(follow=['my_fk_relation', 'other_fk_relation'])
    class MyModel(models.Model):
        ...

This would also add related objects into revision's content. **Note** that they
should also be registered with reversions!

For tha admin, simply replace ``PlaceholderAdminMixin`` with
``VersionedPlaceholderAdminMixin`` to your Admin class for any model's that
include placeholders that should be versioned like so: ::

    from aldryn-reversion.admin import VersionedPlacholderAdminMixin

    class MyModelAdmin(VersionedPlacholderAdminMixin, admin.ModelAdmin):
        ...

You can access revisions from model's admin change form.
**Important** with current version of Aldryn Reverion when you will restore
certain revision you will also restore all objects that are present in the same
revision to a state which was saved with that revision.

You can access recover view form model's admin change list view. Recover view
will allow you to restore deleted object with translations that are belong to
it. Also if FK relations were registered with `follow` property and they are
required for this object - they should be restored also. If user has an ability
to restore required objects manually - he will need to restore them manually,
otherwise they will be restored automatically to state at that revision.

Options
~~~~~~~

``follow_placeholders`` - The 'follow_placeholders' class property is
introduced and is, by default, True. If set to False in the implmementing class
allows the class to implement reversion, but without considering the placeholder
field(s) it contains.

To apply aldryn-reversion to a class but ignore the contents of its
placeholderfield(s), register it like so: ::

    @reversion.register(
        adapter_cls=ContentEnabledVersionAdapter,
        follow_placeholders=False,
        revision_manager=reversion.default_revision_manager,
    )
    class MyModel(models.Model):
        # Changes to plugins inside this placeholder fields are not revisioned
        # but theif we change the placeholder object this field points to, that
        # change will be picked up by reversion.
        placeholder = PlaceholderField()

instead of using the shortcut decorator ``@version-controlled-content``.

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
