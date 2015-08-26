#############################
How it works and known issues
#############################

Django reversion provides a set of models and tools to save model change
history in a way that allows to revert changes or recover deleted object.

Aldryn Reversion is an extension that adds additional features and allows
to handle more information that is not possible with plain django-reversion
i.e. Django-cms placeholder fields or translatable parler fields.

This is possible because of additional logic to add those models into revision
context (via adding those models to follow).

~~~~~~~~~~~~~~~~~~
Revert and recover
~~~~~~~~~~~~~~~~~~

Be aware that currently reverting revision just reverts all versions that are
related to selected revision (history point). Because of that you might be in
a situation where all FK fields that were followed would be reverted to same
historical point as a side effect.

Another edge case is related to model registration. If you did not registered
model's FK that are required (blank=False) and those related objects would be
deleted at the moment of reverse or recover actions that would lead to database
``IntegrityError``. To avoid that you need to always register your FKs with
passing their names to follow keyword argument for
``version_controlled_content`` as mentionned in :doc:`how_to/usage`.

~~~~~~~~~~~~~~~~~~
Admin registration
~~~~~~~~~~~~~~~~~~

If you cannot see ``recover deleted`` button on model's changelist admin view
or you cannot access 'history revert' mechanism - most likely this model is not
registered with ``VersionedPlaceholderAdminMixin`` like described in
:doc:`how_to/usage`.

If that is the case be aware that in case of conflicts on required FKs
current conflict auto resolving mechanism would still try to restore other
models (required FK relation to a model that is not registered with admin
mixin) in an automatic way. The logic is pretty simple in that case.
Conflict resolver would try to resolve conflicts in a recursive way and
restore deleted object first. If that is not possible you would get an
``IntegrityError``.
