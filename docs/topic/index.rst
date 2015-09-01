##########
Key topics
##########


***********
Limitations
***********

Revert and recover
==================

Be aware that reverting a model instance will also revert all related (i.e. via a foreign key)
object instances to the same history point - this will not always be the desired behaviour, and may
not be what is expected by your site's content editors.


Possible database integrity errors
==================================

If:

* a model has non-nullable foreign keys (``null=False``), *and*
* these foreign keys are not registered using the :ref:`follow` option, *and*
* a reversion action deletes a related object

then you will face a database ``IntegrityError``.

To avoid this, ensure that such foreign keys are registered using the the :ref:`follow` keyword.


*********************
Missing admin options
*********************

If the **Recover deleted** button on a model's changelist admin view seems to be missing,
or you cannot access the *history revert* mechanism, then most likely this model has not
been correctly registered with ``VersionedPlaceholderAdminMixin``. See :ref:`admin_registration`
