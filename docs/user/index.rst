######################
Using Aldryn Reversion
######################

After you set up and configured your models (they are registered for revisions
support) you can start using ``aldryn-reversion`` end-user features.

************************
Restoring object version
************************

Most likely you already know that django keeps track of object changes also
known as history, it is available on object admin edit form on the top of the
page. With ``aldryn-reversion`` that history has more features.
As soon as object is created - 'Initial version' is created and treated as
restore point.

Each record in history has a date which is now a link to restore revision
form.
When you need to restore any object version you just need to click on desired
date, check what will be changed  and either restore that revision or go back
to object history.

.. note::
    Be aware that in current implementation revision is restored as is.
    That means that any related object that is also stored in this revision
    would be restored at the point at which that object was stored.
    This is applicable to whole relation tree (if follow was configured).

As soo as you restore object version the object would be at the version at
which it was kept and you will be redirected to object edit form so that you
can change object if you need to.

You might also want to change related object (if applicable) since they also
will be affected.

.. note::
   If :ref:`follow` was not configured properly and related object was not
   stored in selected revision - you might end up with getting an
   ``IntegrityError``. In this case you first need to restore related object
   that was deleted.


*************************
Recovering deleted object
*************************

Second most powerful feature of ``aldryn-reversion`` is to recover deleted
objects.
You may find it on model's change list page after clicking on the
``Recover deleted`` button on top of that page.

If there are deleted objects (which do not exist in database but there is an
object version stored with reversions) they will be listed on recover page.

To recover deleted object simply choose an object, check the recover page
instructions and if there is no conflicts on related fields (FKs) click on
recover button with a label of ``Yes, I'm sure``.

However if there are any conflicts that might be resolved by user (object
model was registered with ``aldryn-reversions`` decorator AND a with admin
mixin for model admin registration) you will see a list of links to recover
related objects first.

.. note::
    In current implementation only required FKs are considered as a conflicts,
    but this would be changed in next versions since if relation existed for
    not required FK, and related object was deleted you will end up with
    ``IntegrityError`` when you will try to restore this object.
    In such cases if you know which related object is missing and if it was
    registered with ``aldryn-reversion`` for revision tracking and with admin
    mixin - you can recover related object first and then return to restore
    this object.

In case if related object was not registered with admin mixin but it was
registered for revision tracking ``aldryn-reversion`` would try to solve
conflict automatically by examining required FK relations.
In case of success you might be able to restore the object and objects that
are required relations to this object.

.. note::
    Be aware that automatic resolver would try to use selected object reivison
    which means that related objects would be restored at version at which
    they were in that revision (not the object latest version).
    So be sure to examine related objects and edit them to the desired state.

****************************
Translations (django-parler)
****************************

If model that is registered with ``aldryn-reversion`` contains translatable
fields each form (restore object version and recover deleted object) will
also have a choice to select translations to restore.
In that case at least one translation should be selected.

*********************
CMS placeholder field
*********************

If model has ``placeholder`` fields and ``aldryn-reversion`` was not
configured to ignore those fields they will also be tracked as a part of
object revision.
That means that in case if placeholder object that represents model's
placeholder field would be deleted - you will be notified that it will be
restored (in case of recover process).

.. note::
    If only placeholder object was deleted (not the plugins that it holds)
    then you will be able to get palceholder AND plugins, most likely
    plugins were not changed (relation to placeholder).
    But if palceholder AND related plugins were deleted then restoring
    placeholder object won't restore the plugins, which means that it will
    be just an empty placeholder. Though you might be able to restore plugins
    as well if after recovering deleted object you will restore object version
    which contains plugins as well.

In case of reverting history it would be restored to selected objcet version
revision automatically. That is happening due to current revert implementation.
That means that you might be interested to checking and/or editing restored
object and it's plugins content.
