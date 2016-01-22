# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db.models.fields.related import ForeignKey
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _

from reversion.revisions import default_revision_manager

from cms.models import CMSPlugin, Placeholder
from cms.models.fields import PlaceholderField


def object_is_reversion_ready(obj):
    """
    Returns True if the object's model
    is registered with Django reversion.
    """
    cls = obj.__class__
    return default_revision_manager.is_registered(cls)


def object_is_translation(obj):
    """
    Returns True if object is translation object.
    """
    related_name = getattr(obj, 'related_name', None)
    if related_name is None:
        return False
    if related_name != 'translations':
        return False
    return True


def build_obj_repr(obj):
    """
    Returns a unicode string of object Model name and its text representation.
    """
    return "{0}: '{1}'".format(force_text(obj._meta.model.__name__),
                               force_text(obj))


def get_translation_info_message(obj):
    """
    Prepares a simple translation info message i.e " ('EN' translation)"
    for given object, or an empty string.
    """
    language_message = ''
    if getattr(obj, 'language_code', None) is not None:
        language_message = _(" ('%(language_code)s' translation)") % {
            'language_code': obj.language_code.upper()}
    return language_message


def get_translations_versions_for_object(obj, revision, versions=None):
    """
    Returns a queryset of translation versions for given object, if versions
    provided - performs lookup on them instead of revision.version_set.all().
    """
    translatable = hasattr(obj, 'translations')
    if not translatable:
        return []

    if versions is None:
        versions = revision.version_set.all()
    # get translations versions
    translation_model = obj.translations.model
    translation_ct = ContentType.objects.get_for_model(translation_model)
    translation_version = versions.filter(content_type=translation_ct)
    return translation_version


def get_fk_models(obj, blank=None):
    """
    Returns a list of tuples (FK model, `blank`) for FK relations on a given
    object model. If blank is provided - filters by `blank` attribute value.
    :param obj: object to check FK relations
    :param blank: bool to filter relations by `blank` FK attrubute
    :return: list of tuples (FK model, fk.blank)
    """
    fk_relations = []
    for fk in obj._meta.fields:
        # process only FK and subclasses
        if not issubclass(type(fk), ForeignKey):
            continue
        if fk.blank == blank or blank is None:
            relation = {
                'fk_field': fk,
                'model': fk.rel.to,
                'content_type': ContentType.objects.get_for_model(fk.rel.to),
                'blank': fk.blank,
            }
            fk_relations.append(relation)
    return fk_relations


def get_deleted_objects_versions(versions):
    """
    Returns a list of version for deleted objects in given versions queryset.
    Performs excluding on versions queryset if exclude dictionary
    {field_name: value, ...} is provided.
    """
    deleted_versions = []
    for version in versions:
        if object_was_deleted(version):
            deleted_versions.append(version)
    return deleted_versions


def object_was_deleted(version):
    if version.object is None:
        # if there is no relation to object - it is delted
        return True
    # in case if GenericKey relation is broken, or object was takem
    # from cache - try to perform DB lookup. This will/should always hit db.
    # get object model class to access database for lookup
    check_obj_model = version.object._meta.model
    # if there is a match - object exists and we don't need to
    # restore it
    if check_obj_model.objects.filter(pk=version.object_id).count() == 0:
        return True
    return False


def get_conflict_fks_versions(obj, version, revision, exclude=None):
    """
    Lookup for deleted FKs for obj, expects version to be obj
    version from the same revision.
    If exclude provided - excludes based on that from versions to check.
    Expects exclude to be a dict of filter string, value i.e {'pk': 1}.
    Returns versions for deleted fks.
    """
    # TODO: get all conflicts, return a tuple/dict with required and not.
    fk_relations = get_fk_models(obj)
    versions_to_check = []
    for relation in fk_relations:
        found_versions = revision.version_set.exclude(
            pk=version.pk).filter(content_type=relation['content_type'])
        versions_to_check += list(found_versions.values_list('pk', flat=True))

    # convert to versions queryset instead of a list
    versions_to_check_qs = revision.version_set.filter(pk__in=versions_to_check)

    if exclude is not None:
        versions_to_check_qs = versions_to_check_qs.exclude(**exclude)

    conflict_fks_versions = get_deleted_objects_versions(
        versions_to_check_qs)
    return conflict_fks_versions


def object_has_placeholders(obj):
    """
    Returns True if given object has placeholder fields, False otherwise.
    """
    return PlaceholderField in [type(field)
                                for field in obj._meta.fields]


def get_placeholder_fields_names(obj):
    return [field.name for field in obj._meta.fields
            if type(field) == PlaceholderField]


def get_deleted_placeholders(revision):
    """
    Lookup for deleted placeholders for given revision
    """
    placeholder_ct = ContentType.objects.get_for_model(Placeholder)
    placeholder_versions = revision.version_set.filter(
        content_type=placeholder_ct)
    deleted_placeholders = get_deleted_objects_versions(placeholder_versions)
    return deleted_placeholders


def get_placeholders_from_obj(obj):
    placeholders_pks = [getattr(obj, '{0}_id'.format(field_name))
                        for field_name in get_placeholder_fields_names(obj)]
    return Placeholder.objects.filter(pk__in=placeholders_pks)


def get_deleted_placeholders_for_object(obj, revision):
    """
    Return deleted placeholders for object given
    """
    if object_has_placeholders(obj):

        placeholders_versions = get_deleted_placeholders(revision)
        # add only placeholders that belong to this object,
        # accessing field_name itself refers to deleted object, but _id isn't.
        # Other approach would be to load object_repr and get data from there
        placeholders_pks = [getattr(obj, '{0}_id'.format(field_name))
                            for field_name in get_placeholder_fields_names(obj)
                            if getattr(obj,
                                       '{0}_id'.format(field_name),
                                       None) is not None]
        return [placeholder_version
                for placeholder_version in placeholders_versions
                if placeholder_version.object_id_int in placeholders_pks]
    return []


def exclude_resolved(to_exclude, objects):
    """
    Exclude items that are in to_exclude from objects, excepts both to be list
    of revision.models.Versions.
    """
    return [item for item in objects if item not in to_exclude]


def sync_placeholder_version_plugins(obj, version):
    plugin_c_type_id = ContentType.objects.get_for_model(CMSPlugin).pk
    placeholders = get_placeholders_from_obj(obj).values_list('pk', flat=True)

    # Get all versions that belong to the same revision as
    # the given version object.
    related_versions = version.revision.version_set.iterator()

    # List of all plugin ids in this revision
    plugin_ids = [v.object_id for v in related_versions
                  if v.content_type_id == plugin_c_type_id]

    # Remove plugins that are not part of the revision.
    old_plugins = (
        CMSPlugin
        .objects
        .filter(placeholder__in=placeholders)
        .exclude(pk__in=plugin_ids)
    )
    old_plugins.delete()


class RecursiveRevisionConflictResolver(object):

    def __init__(self, version, to_resolve=None, exclude=None):
        self.resolved = []
        self.version = version
        if to_resolve is None:
            self.to_resolve = []
        else:
            self.to_resolve = to_resolve
        if exclude is not None:
            self.initial_exclude = exclude
        else:
            self.initial_exclude = []

    def _update_resolved(self, versions):
        """
        Update resolved versions.
        :param versions:
        :return:
        """
        for version in versions:
            if version not in self.resolved:
                self.resolved.append(version)

    def _update_to_resolve(self, other_conflicts):
        for item in other_conflicts:
            if item not in self.resolved and item not in self.initial_exclude:
                self.to_resolve.append(item)

    def resolve(self, version=None):

        if version is None:
            version = self.version

        obj = version.object_version.object
        revision = version.revision

        self._update_resolved([version])

        other_conflicts = get_conflict_fks_versions(obj, version, revision)

        deleted_placeholders = get_deleted_placeholders_for_object(obj,
                                                                   revision)
        if deleted_placeholders:
            self._update_resolved(deleted_placeholders)

        # check for translations
        translatable = hasattr(obj, 'translations')
        if translatable:
            translation_versions = get_translations_versions_for_object(
                obj, revision)
            self._update_resolved(translation_versions)

        # recalculate to resolve.
        self._update_to_resolve(other_conflicts)

        # recursion, we have everything we need
        if self.to_resolve:
            self.resolve(self.to_resolve.pop(0))

        # base case
        if not self.to_resolve:
            return self.resolved
