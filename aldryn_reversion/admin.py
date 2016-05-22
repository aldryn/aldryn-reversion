# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib import messages
try:
    from django.contrib.admin.utils import unquote
except ImportError:
    # Django<=1.6
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from django.contrib.admin.util import unquote
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _

from cms.admin.placeholderadmin import PlaceholderAdminMixin
from reversion import VERSION as REVERSION_VERSION
from reversion.models import Version
from reversion.admin import VersionAdmin

from .core import create_revision
from .forms import RecoverObjectWithTranslationForm
from .utils import (
    get_conflict_fks_versions, build_obj_repr,
    get_deleted_placeholders_for_object, object_is_translation,
    get_translation_info_message, RecursiveRevisionConflictResolver,
    object_is_reversion_ready,
    object_has_placeholders,
    sync_placeholder_version_plugins,
)

REVERSION_1_9_OR_HIGHER = REVERSION_VERSION >= (1, 9)


class VersionedPlaceholderAdminMixin(PlaceholderAdminMixin, VersionAdmin):
    revision_confirmation_template = 'aldryn_reversion/confirm_reversion.html'
    recover_confirmation_template = 'aldryn_reversion/confirm_recover.html'

    def add_plugin(self, request):
        with transaction.atomic():
            return super(VersionedPlaceholderAdminMixin, self).add_plugin(
                request)

    def edit_plugin(self, request, plugin_id):
        with transaction.atomic():
            return super(VersionedPlaceholderAdminMixin, self).edit_plugin(
                request, plugin_id)

    def move_plugin(self, request):
        with transaction.atomic():
            return super(VersionedPlaceholderAdminMixin, self).move_plugin(
                request)

    def delete_plugin(self, request, plugin_id):
        with transaction.atomic():
            return super(
                VersionedPlaceholderAdminMixin, self).delete_plugin(
                request, plugin_id)

    def get_commen_plugin_info(self, plugin):
        """
        Returns a dict with plugin info (to use in comment for revision)
        """
        return {'plugin_id': plugin.id, 'plugin': force_text(plugin)}

    def _create_aldryn_revision(self, target, user=None,
                                comment=None, source=None):
        #
        # _get_attached_objects returns the models which define the
        # PlaceholderField to which this placeholder is linked. Theoretically it
        # is possible to have a placeholder attached to multiple models (as two
        # PlaceholderFields could point to the same instance), but the only way
        # to do this is by coding it. As we don't support this use case yet,
        # better to fail loudly than to compromise the integrity of the data by
        # applying the versioning to the wrong model.
        #

        get_attached_object = self._get_placeholder_attached_object

        obj_from_target = get_attached_object(target)

        if source:
            obj_from_source = get_attached_object(source)
        else:
            obj_from_source = None

        if not obj_from_target and not obj_from_source:
            return

        if obj_from_target and object_is_reversion_ready(obj_from_target):
            create_revision(obj_from_target, user=user, comment=comment)

        if (obj_from_source and obj_from_source != obj_from_target and
                object_is_reversion_ready(obj_from_source)):
            create_revision(obj_from_source, user=user, comment=comment)

    def _get_placeholder_attached_object(self, placeholder):
        objs = placeholder._get_attached_objects()

        # _get_attached_objects returns the models which define the
        # PlaceholderField to which this placeholder is linked. Theoretically it
        # is possible to have a placeholder attached to multiple models (as two
        # PlaceholderFields could point to the same instance), but the only way
        # to do this is by coding it. As we don't support this use case yet,
        # better to fail loudly than to compromise the integrity of the data by
        # applying the versioning to the wrong model.

        assert len(objs) <= 1, 'Placeholder attached to multiple objects'

        try:
            obj = objs[0]
        except IndexError:
            obj = None
        return obj

    def post_clear_placeholder(self, request, placeholder):
        comment_dict = {'placeholder': placeholder}
        comment = _('All plugins in the placeholder '
                    '"%(placeholder)s" were deleted.') % comment_dict

        self._create_aldryn_revision(placeholder, request.user, comment)

    def post_add_plugin(self, request, *args):
        # The signature for post_add_plugin
        # prior to 3.3 was request, placeholder, plugin.
        # On 3.3 this was changed to request, plugin
        # to keep consistency with the other hook methods.
        try:
            # CMS <= 3.2.x
            placeholder, plugin = args
        except ValueError:
            # CMS >= 3.3.x
            plugin = args[0]
        comment_dict = self.get_commen_plugin_info(plugin)
        comment = _('Added plugin #%(plugin_id)s: %(plugin)s') % comment_dict
        self._create_aldryn_revision(plugin.placeholder, request.user, comment)

    def post_edit_plugin(self, request, plugin):
        comment_dict = self.get_commen_plugin_info(plugin)
        comment = _('Edited plugin #%(plugin_id)s: %(plugin)s') % comment_dict
        self._create_aldryn_revision(plugin.placeholder, request.user, comment)

    def post_copy_plugins(self, request, source_placeholder, target_placeholder,
                          plugins):
        comment_dict = {'placeholder': target_placeholder}
        comment = _("Copied plugins to %(placeholder)s") % comment_dict
        # We pass None because copy operations do not modify
        # the source placeholder in any way, so no need
        # to create a revision for the source.
        self._create_aldryn_revision(
            target_placeholder,
            request.user,
            comment,
            source=None,
        )

    def post_move_plugin(self, request, source_placeholder, target_placeholder,
                         plugin):
        comment_dict = {'placeholder': target_placeholder}
        comment = _('Moved plugins to %(placeholder)s') % comment_dict
        self._create_aldryn_revision(
            target_placeholder,
            request.user,
            comment,
            source=source_placeholder
        )

    def post_delete_plugin(self, request, plugin):
        comment_dict = self.get_commen_plugin_info(plugin)
        comment = _('Deleted plugin #%(plugin_id)s: %(plugin)s') % comment_dict
        self._create_aldryn_revision(plugin.placeholder, request.user, comment)

    def log_addition(self, request, obj, change_message=None):
        """
        Override reversion.VersionAdmin log addition to provide useful message.
        """
        comment = _(
            "Initial version of %(object_repr)s.%(translation_info)s") % {
                'object_repr': build_obj_repr(obj),
                'translation_info': get_translation_info_message(obj)}
        # starting from django-reversion 1.9 revision is created in add view
        # so there is no need to do that manually, but we want to have
        # our meaningful comment instead of the standard one.
        if REVERSION_1_9_OR_HIGHER:
            class_super = VersionedPlaceholderAdminMixin
        else:
            # Prior to django-reversion 1.9.0 there were no way to change
            # initial comment, but we still need call super to invoke django's
            # log_addition and avoid django-reversion log_addition.
            class_super = VersionAdmin
        try:
            super(class_super, self).log_addition(request, obj, comment)
        except TypeError:  # Django < 1.9 pragma: no cover
            super(class_super, self).log_addition(request, obj)

        # For older reversions we still need to do revision manually.
        if REVERSION_1_9_OR_HIGHER:
            return

        # previous implementation was to use self.get_revision_data
        # but that was also removed in 1.9.0 since it was a duplicate of logic
        # that is already present in save_revision or its related calls.
        self.revision_manager.save_revision(
            [obj],
            user=request.user,
            comment=comment,
            ignore_duplicates=self.ignore_duplicate_revisions,
            db=self.revision_context_manager.get_db(),
        )

    def log_change(self, request, obj, message, deletion=False):
        # prepare correct change message so that we can distinguish which
        # revision would be restored. if object has language code - apppend
        # it to the message, but if previous operation was translation deletion
        # do not modify the message, it is already prepared.
        if not deletion:
            message = "{0} {1}{2}".format(
                message, build_obj_repr(obj), get_translation_info_message(obj))
        super(VersionedPlaceholderAdminMixin, self).log_change(
            request, obj, message)

    # TODO: extract to separate translation admin mixin
    def log_deletion(self, request, obj, object_repr):
        # skip not translation objects, we don't need to do anything on regular
        # objects
        if not object_is_translation(obj):
            super(VersionedPlaceholderAdminMixin, self).log_deletion(
                request, obj, object_repr)
            return

        # django-reversion does not provides you with log deletion,
        # for recover view it just uses diff between real objects
        # and the last revision objects for given model.
        # Instead wev will use log_change for translation master object
        message = _(
            "Translation deletion for %(object_repr)s "
            "('%(lang_code)s' language).") % {
                'object_repr': build_obj_repr(obj.master),
                'lang_code': obj.language_code.upper()}
        self.log_change(request, obj.master, message, deletion=True)

    @transaction.atomic
    def revision_view(self, request, object_id, version_id,
                      extra_context=None):
        if not self.has_change_permission(request):
            raise PermissionDenied()

        obj = get_object_or_404(self.model, pk=unquote(object_id))
        version = get_object_or_404(Version, pk=unquote(version_id),
                                    object_id=force_text(obj.pk))
        revision = version.revision

        if request.method == "POST":
            revision.revert()

            if object_has_placeholders(obj):
                sync_placeholder_version_plugins(obj, version)
            opts = self.model._meta
            pk_value = obj._get_pk_val()
            preserved_filters = self.get_preserved_filters(request)

            msg_dict = {
                'name': force_text(opts.verbose_name),
                'obj': force_text(obj)
            }
            msg = _('The %(name)s "%(obj)s" was successfully reverted. '
                    'You may edit it again below.') % msg_dict
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = reverse(
                'admin:%s_%s_change' % (opts.app_label, opts.model_name),
                args=(pk_value,),
                current_app=self.admin_site.name
            )
            redirect_url = add_preserved_filters({
                'preserved_filters': preserved_filters,
                'opts': opts,
            }, redirect_url)
            return HttpResponseRedirect(redirect_url)
        else:
            context = {
                'object': obj,
                'version': version,
                'revision': revision,
                'revision_date': revision.date_created,
                'versions': revision.version_set.order_by(
                    'content_type__model', 'object_id_int').all,
                'object_name': force_text(self.model._meta.verbose_name),
                'app_label': self.model._meta.app_label,
                'opts': self.model._meta,
                'add': False,
                'change': True,
                'save_as': False,
                'has_add_permission': self.has_add_permission(request),
                'has_change_permission': self.has_change_permission(
                    request, obj),
                'has_delete_permission': self.has_delete_permission(
                    request, obj),
                'has_file_field': True,
                'has_absolute_url': False,
                'original': obj,
            }
            return render_to_response(self.revision_confirmation_template,
                                      context, RequestContext(request))

    @transaction.atomic
    def recover_view(self, request, version_id, extra_context=None):
        if not self.has_change_permission(request):
            raise PermissionDenied()

        version = get_object_or_404(Version, pk=unquote(version_id))
        obj = version.object_version.object
        revision = version.revision

        # check for conflicts, it is better that user would solve them
        conflict_fks_versions = get_conflict_fks_versions(
            obj, version, revision)

        # build urls to point user onto restore links for conflicts
        opts = self.model._meta
        non_reversible_by_user = []
        conflicts_links_to_restore = []
        for fk_version in conflict_fks_versions:
            # try to point user to conflict recover views
            try:
                link = reverse(
                    'admin:{0}_{1}_recover'.format(
                        opts.app_label,
                        fk_version.object_version.object._meta.model_name),
                    args=[fk_version.pk])
                link_dict = {
                    'version': fk_version,
                    'link': link
                }
            except NoReverseMatch:
                # if there is exception either model is not registered
                # with VersionedPlaceholderAdminMixin or there is no admin
                # for that model. In both cases we need to revert this object
                # to avoid conflicts / integrity errors
                non_reversible_by_user.append(fk_version)
            else:
                conflicts_links_to_restore.append(link_dict)

        # check if we need to restore placeholder fields
        object_placeholders = get_deleted_placeholders_for_object(obj, revision)
        # if there are conflicts that cannot be resolved manually by the user
        # rely on resolver.
        if len(non_reversible_by_user) > 0:
            non_reversible_by_user = RecursiveRevisionConflictResolver(
                non_reversible_by_user[0], non_reversible_by_user[1:]).resolve()

        # prepare form kwargs
        restore_form_kwargs = {
            'revision': revision,
            'obj': obj,
            'version': version,
            'resolve_conflicts': non_reversible_by_user,
            'placeholders': object_placeholders
        }

        if request.method == "POST":
            form = RecoverObjectWithTranslationForm(request.POST,
                                                    **restore_form_kwargs)
            # form.is_valid would perform validation against foreign keys
            if form.is_valid():
                # form save will restore desired versions for object and its
                # translations
                form.save()
                # FIXME: optimize response
                opts = self.model._meta
                pk_value = obj._get_pk_val()
                preserved_filters = self.get_preserved_filters(request)

                msg_dict = {
                    'name': force_text(opts.verbose_name),
                    'obj': force_text(obj)
                }
                msg = _('The %(name)s "%(obj)s" was successfully recovered. '
                        'You may edit it again below.') % msg_dict
                self.message_user(request, msg, messages.SUCCESS)
                redirect_url = reverse(
                    'admin:%s_%s_change' % (opts.app_label, opts.model_name),
                    args=(pk_value,),
                    current_app=self.admin_site.name
                )
                # TODO: Check if there is next parameter and redirect to
                # next, for cases of conflict solving.
                redirect_url = add_preserved_filters({
                    'preserved_filters': preserved_filters,
                    'opts': opts,
                }, redirect_url)
                return HttpResponseRedirect(redirect_url)
        else:
            # populate form with regular data
            form = RecoverObjectWithTranslationForm(**restore_form_kwargs)

        context = {
            'object': obj,
            'version': version,
            'revision': revision,
            'revision_date': revision.date_created,
            'conflict_links': conflicts_links_to_restore,
            'non_resolvable_conflicts': non_reversible_by_user,
            'placeholders_to_restore': object_placeholders,
            'versions': revision.version_set.order_by(
                'content_type__name', 'object_id_int').all,
            'object_name': force_text(self.model._meta.verbose_name),
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'add': False,
            'change': True,
            'save_as': False,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(
                request, obj),
            'has_delete_permission': self.has_delete_permission(
                request, obj),
            'has_file_field': True,
            'has_absolute_url': False,
            'original': obj,
        }
        # if there is no conflicts - add form to context.
        if not conflicts_links_to_restore:
            context['restore_form'] = form
        return render_to_response(self.recover_confirmation_template,
                                  context, RequestContext(request))
