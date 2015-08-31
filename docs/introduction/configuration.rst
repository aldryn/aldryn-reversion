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

    @version_controlled_content(follow=['my_fk_field'])
    class MyModel(models.Model):
        my_fk_field = models.ForeignKey(OtherModel)
        ...


This also adds the related objects as version-controlled content.

.. note:: These related models should also be registered with django-reversion in their own right.



Options
=======

If you need more control over exactly what is versioned, then use ``@reversion.register()`` rather
than the ``@version-controlled-content`` decorator.


``follow_placeholders``
-----------------------

By default, a model's Placeholder fields are versioned (in case of using
``@version-controlled-content`` decorator). Setting ``follow_placeholders``
to ``False`` disables this behaviour. In this case *changes to plugins inside
this placeholder* fields are not revisioned but if we change the placeholder
object this field points to, that change will be picked up by reversion.

Pass this option when registering the model with reversion::

    @reversion.register(
        adapter_cls=ContentEnabledVersionAdapter,
        follow_placeholders=False,
        revision_manager=reversion.default_revision_manager,
    )
    class MyModel(models.Model):
        ...
        placeholder = PlaceholderField()



.. _follow:

``follow``
----------

If yor model has FK relations you can use ``follow`` property from
``django-reversions`` when applying decorator: ::

    @version_controlled_content(follow=['my_fk_relation', 'other_fk_relation'])
    class MyModel(models.Model):
        ...
        my_fk_relation = models.ForeignKey(OtherModel)
        other_fk_relation = models.ForeignKey(OtherModel)


In fact you should be able to also use other ``django-reversion`` options that
are available for ``revision.register`` as described in
`Advanced model registration
<http://django-reversion.readthedocs.org/en/latest/api.html#advanced-model-registration>`_


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
