######################
Using Aldryn Reversion
######################

After you have set up and configured your models so that they are registered
for revision support you can start using the ``aldryn-reversion``
end-user features.


*************************
Restoring object versions
*************************

Django already keeps track of changes to objects and makes their history available in the object's
qadmin edit form. With ``aldryn-reversion`` that history has more features.

As soon as an object is created, an *Initial version* is created and treated as
a restore point.

For each record in an object's history you'll now find a link to the
*restore revision* form.

To restore a previous object version, select the desired date, check what will
be changed, and if you are satisfied with the proposed changes, confirm to
restore the revision.

.. note::

   Note that the revision will be restored *as is* - all objects related to the object you are
   restoring will also be restored to the same revision. That means that any related object that is
   also stored in this revision would be restored to the point at which that object was stored.

   This will be applicable to entire relation tree (if ``follow`` was configured).

Once the the object is restored its content will be set to the revision you've
chosen and you will be redirected to the object's edit form.

You might also want to modify some of the related objects, since they too
will be affected by restoring to a previous revision.

.. note::

   If :ref:`follow` was not configured properly and as a result the related
   objects were not stored as part of the selected revision, you could end
   up with an ``IntegrityError``. In such a case you will first need
   to restore the related object.


**************************
Recovering deleted objects
**************************

Another powerful feature of ``aldryn-reversion`` is the ability to
recover deleted objects.

This function is available on a model's change list page - a
*Recover deleted* option is available near the top of the page.

If there are any deleted objects which do not currently exist in the database but for
which there is a version stored by reversions, they will be listed on the
recovery page.

To recover a deleted object, simply choose an object, check the instructions
and if there are no conflicts for the related fields select the **Yes, I'm sure** button.

If there are any conflicts that can be resolved by the user (the model was
registered with the ``aldryn-reversions`` decorator and with admin mixin)
the user will be presented with a list of links for recovering the related
objects first.

.. note::
    In current implementation only required FKs are considered as a conflicts,
    but this would be changed in next versions since if relation existed for
    not required FK, and related object was deleted you will end up with
    ``IntegrityError`` when you will try to restore this object.

    In such cases if you know which related object is missing and if it was
    registered with ``aldryn-reversion`` for revision tracking and with admin
    mixin - you can recover related object first and then return to restore
    this object.

If a related object was not registered with the admin mixin but was
registered for revision tracking ``aldryn-reversion`` will attempt to resolve
the conflict automatically by examining the required FK relations.
If automatic conflict resolution was successful you will be able to restore
the object and its required relations.

.. note::

    Note that automatic conflict resolution will try to use the selected
    object revision. Related objects will be restored to the version at
    which they were in that revision - not the object's latest version.
    Be sure to examine the related objects carefully and edit them so that
    they are in the desired state.


****************************
Translations (django-parler)
****************************

When a model that is registered with ``aldryn-reversion`` contains translatable
fields, recover form  will also have the option to select translations
to restore.
In that case at least one translation should be selected.

*********************
CMS placeholder field
*********************

If a model has ``placeholder`` fields and ``aldryn-reversion`` was not
configured to ignore those fields, they will also be tracked as part of
object's revision.

In such cases, when the placeholder object representing the parent model's
placeholder field is deleted, you will be notified and it will be restored as
part of the recovery process.

.. note::
    If only the placeholder object is deleted (and not the plugins that it
    holds) you will be able to restore both the placeholder and the
    plugins - in most cases the plugins will not have changed. If, on the
    other hand, both the placeholder and the related plugins were deleted,
    the result would be an empty placeholder. You may still be able to
    restore the plugins if, after recovering the deleted object, you restore
    an object version which contains the plugins.

When reverting history, the object will be restored to the corresponding
revision automatically, so it may be a good idea to check the restored
object and its plugins and edit them where necessary.
