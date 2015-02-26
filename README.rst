================
Aldryn Reversion
================


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

For tha admin, simply replace ``PlaceholderAdminMixin`` with
``VersionedPlaceholderAdminMixin`` to your Admin class for any model's that
include placeholders that should be versioned like so: ::

    from aldryn-reversion.admin import VersionedPlacholderAdminMixin

    class MyModelAdmin(VersionedPlacholderAdminMixin, admin.ModelAdmin):
        ...

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
