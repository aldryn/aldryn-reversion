#####
Usage
#####

Using Aldryn Reversion in your project is relatively simple.

There are two parts. Adding a registration decorator to your model and adding a
mixin to your admin class definition for the same model.

******************
Model registration
******************

For the model, add ``version_controlled_content`` as a decorator like so: ::

    from aldryn-reversion.core import version_controlled_content

    @version_controlled_content
    class MyModel(models.Model):
        ...

If yor model has FK relations you can use `follow` property from
`django-reversions` when applying decorator: ::


    class MyModel(models.Model):
        ...

This would also add related objects into revision's content. **Note** that they
should also be registered with reversions!

******************
Admin registration
******************

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

************
Custom usage
************

In case if you need to make your own custom decorator to register only
translaions or placeholders or something other but still use advantages that
Aldryn reversion ships - you can construct your own decorator by mixing
``core`` mixins in same manner or by usng reversion.register with custom
configuration using :doc:`how_to/options` as an example.