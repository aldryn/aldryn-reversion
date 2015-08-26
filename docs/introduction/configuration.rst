##############################
Apply Aldryn Reversion support
##############################

Using Aldryn Reversion in your project is fairly strightforward.

There are two key steps required:

* applying a registration decorator to your model
* adding a mixin to the model's admin class definition


******************
Model registration
******************

For the model, add ``@version_controlled_content`` as a decorator::

    from aldryn-reversion.core import version_controlled_content

    @version_controlled_content
    class MyModel(models.Model):
        ...

If your model has foreign key relations, use the ``follow`` property from
``django-reversions`` when applying the decorator::

    class MyModel(models.Model):
        ...

.. todo:: this seems to be missing ^^^

This also add the related objects as version-controlled content.

.. todo:: We need to explain why related models should *also* be registered independently

.. note:: These related models should also be should also be registered with django-reversion in their own right.


Options
=======

If you need more control over exactly what is versioned, then use ``@reversion.register()`` rather
than the ``@version-controlled-content`` decorator.


``follow_placeholders``
-----------------------

By default, a model's Placeholder fields are versioned. Setting ``follow_placeholders`` to
``False`` disables this behaviour. Pass this option when registering the model with reversion::

    @reversion.register(
        adapter_cls=ContentEnabledVersionAdapter,
        follow_placeholders=False,
        revision_manager=reversion.default_revision_manager,
    )
    class MyModel(models.Model):
        ...

.. todo:: The following comment is unclear

        # but theif we change the placeholder object this field points to, that
        # change will be picked up by reversion.
        placeholder = PlaceholderField()


.. _follow:

``follow``
----------

.. todo:: use of follow needs to be documented

.. todo:: What other arguments can be passed?


.. _admin_registration:

******************
Admin registration
******************

For the admin, replace ``PlaceholderAdminMixin`` with ``VersionedPlaceholderAdminMixin`` to the
``ModelAdmin`` class for any models that include Placeholders that need to be versioned::

    from aldryn-reversion.admin import VersionedPlacholderAdminMixin

    class MyModelAdmin(VersionedPlacholderAdminMixin, admin.ModelAdmin):
        ...

Revisions are accessible from the model's admin change form.

.. important::

   With the current version of Aldryn Reversion, in restoring a revision you will **also** restore
   all objects that belong to that revision to the state in which they were saved with that
   revision. This behaviour may not be expected by end-users.


Deleted objects
===============

If an object has been deleted, its admin change form will obviously no longer be available.

However, the model's admin change list view offers a **Recover view**, that
allows you to restore a deleted object along with the translations that belong to
it.

If foreign key relations have been registered with the ``follow`` property and they are
required for this object, they too will be restored automatically, to the state captured in the
relevant revision.

