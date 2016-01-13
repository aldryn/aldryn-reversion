# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Support for django-reversion on models with translatable fields and django-cms
placeholder fields.
"""
from functools import partial

from django.db.models.signals import post_save

from cms.models.pluginmodel import CMSPlugin
from reversion.revisions import (
    default_revision_manager, revision_context_manager, VersionAdapter)

# We would like this to not depend on Parler, but still support if it is
# available.
try:
    from parler import cache
except:
    pass


def _add_to_context(obj, manager=None, context=None):
    if manager is None:
        manager = default_revision_manager

    if context is None:
        context = default_revision_manager._revision_context_manager

    adapter = manager.get_adapter(obj.__class__)
    version_data = adapter.get_version_data(obj)
    context.add_to_context(manager, obj, version_data)


def create_revision(obj, user=None, comment=None):
    with revision_context_manager.create_revision():
        if user:
            revision_context_manager.set_user(user)
        if comment:
            revision_context_manager.set_comment(comment)

        _add_to_context(obj)

        if hasattr(obj._meta, 'placeholder_field_names'):
            add_placeholders_to_revision(instance=obj)


def add_placeholders_to_revision(
        instance, revision_manager=None, rev_ctx=None):
    """
    Manually add plugins to the revision.

    This function is an updated version of
    http://github.com/divio/django-cms/blob/develop/cms/utils/helpers.py#L34
    but instead of working on pages, works on models with placeholder
    fields.
    """

    add_to_context = partial(
        _add_to_context,
        manager=revision_manager,
        context=rev_ctx,
    )

    # Add the placeholder to the revision
    for name in instance._meta.placeholder_field_names:
        add_to_context(getattr(instance, name))

    # Add all plugins to the revision
    ph_ids = [getattr(instance, '{0}_id'.format(name))
              for name in instance._meta.placeholder_field_names]

    for plugin in CMSPlugin.objects.filter(placeholder_id__in=ph_ids):
        plugin_instance, _ = plugin.get_plugin_instance()

        if plugin_instance:
            add_to_context(plugin_instance)
        add_to_context(plugin)


class TranslatableVersionAdapterMixin(object):
    revision_manager = None

    def __init__(self, model):
        super(TranslatableVersionAdapterMixin, self).__init__(model)

        # If the model is translated with django-parler, register the
        # translation model to be tracked as well, by following all placeholder
        # fields, if any.
        if hasattr(model, '_parler_meta'):
            root_model = model._parler_meta.root_model
            self.revision_manager.register(root_model)

            # Also add the translations to the models to follow.
            self.follow = list(self.follow) + [model._parler_meta.root_rel_name]

            # And make sure that when we revert them, we update the translations
            # cache (this is normally done in the translation `save_base`
            # method, but it is not called when reverting changes).
            post_save.connect(self._update_cache, sender=root_model)

    def _update_cache(self, sender, instance, raw, **kwargs):
        """Update the translations cache when restoring from a revision."""
        if raw:
            # Raw is set to true (only) when restoring from fixtures or,
            # django-reversion
            cache._cache_translation(instance)


class PlaceholderVersionAdapterMixin(object):
    follow_placeholders = True

    def __init__(self, model):
        super(PlaceholderVersionAdapterMixin, self).__init__(model)

        # Add cms placeholders the to the models to follow.
        placeholders = getattr(model._meta, 'placeholder_field_names', None)

        if self.follow_placeholders and placeholders:
            self.follow = list(self.follow) + placeholders
            post_save.connect(self._add_plugins_to_revision, sender=model)

    def _add_plugins_to_revision(self, sender, instance, **kwargs):
        rev_ctx = self.revision_manager._revision_context_manager

        if rev_ctx.is_active() and not rev_ctx.is_managing_manually():
            add_placeholders_to_revision(
                instance=instance,
                revision_manager=self.revision_manager,
                rev_ctx=rev_ctx,
            )


class ContentEnabledVersionAdapter(TranslatableVersionAdapterMixin,
                                   PlaceholderVersionAdapterMixin,
                                   VersionAdapter):
    pass

version_controlled_content = partial(default_revision_manager.register,
    adapter_cls=ContentEnabledVersionAdapter,
    revision_manager=default_revision_manager)
