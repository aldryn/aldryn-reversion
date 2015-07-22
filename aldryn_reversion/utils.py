# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db.models.fields.related import ForeignKey
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _

import cms.models


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


def get_required_fk_models(obj):
    """
    Returns required (blank=False) FK models for given object.
    """
    fk_fields = [fk for fk in obj._meta.fields if type(fk) == ForeignKey]
    required_fks_models = [fk.rel.to for fk in fk_fields if not fk.blank]
    return required_fks_models


def get_deleted_objects_versions(revision, versions=None,
                                 exclude=None):
    """
    Returns a list of version for deleted objects in given versions queryset,
    or revision.version_set.all() if versions queryset is not provided.
    Performs excluding on versions queryset if exclude dictionary
    (field_name, value) is provided.
    """
    other_deleted = []
    if versions is None:
        revision.version_set.all()

    if exclude is not None:
        versions = versions.exclude(**exclude)

    for version in versions:
        if version.object is None:
            # if there is no relation to object - it is delted
            other_deleted.append(version)
            continue
        # get object model class to access database for lookup
        check_obj_model = version.object._meta.model
        # if there is a match - object exists and we don't need to
        # restore it
        exists = check_obj_model.objects.filter(pk=version.object_id)
        if len(exists) > 0:
            continue
        other_deleted.append(version)
    return other_deleted


def get_conflict_fks_versions(obj, version, revision, exclude=None):
    """
    Lookup for deleted FKs for object
    Returns versions for deleted fks.
    """
    required_models = get_required_fk_models(obj)
    required_cts = [ContentType.objects.get_for_model(
        fk_model) for fk_model in required_models]
    versions_to_check = revision.version_set.exclude(
        pk=version.pk).filter(content_type__in=required_cts)
    conflict_fks_versions = get_deleted_objects_versions(
        revision, versions=versions_to_check, exclude=exclude)
    return conflict_fks_versions


def object_has_placeholders(obj):
    """
    Returns True if given object has placeholder fields, False otherwise.
    """
    return cms.models.PlaceholderField in [type(field)
                                           for field in obj._meta.fields]


def get_placeholder_fields_names(obj):
    return [field.name for field in obj._meta.fields
            if type(field) == cms.models.PlaceholderField]


def get_deleted_placeholders(revision):
    """
    Lookup for deleted placeholders for given revision
    """
    placeholder_ct = ContentType.objects.get_for_model(cms.models.Placeholder)
    placeholder_versions = revision.version_set.filter(
        content_type=placeholder_ct)
    deleted_placeholders = get_deleted_objects_versions(
        revision, versions=placeholder_versions)
    return deleted_placeholders


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


def resolve_conflicts(version, to_resolve):
    """
    Resolve conflicts recursively
    """
    obj = version.object_version.object
    revision = version.revision

    other_conflicts = get_conflict_fks_versions(obj, version, revision)

    resolved_versions = [version]
    deleted_placeholders = get_deleted_placeholders_for_object(obj, revision)
    if deleted_placeholders:
        resolved_versions += deleted_placeholders

    # check for translations
    translatable = hasattr(obj, 'translations')
    if translatable:
        translation_versions = get_translations_versions_for_object(
            obj, revision)
        resolved_versions += list(translation_versions)

    # base case
    if not to_resolve and not other_conflicts:
        return resolved_versions

    # if only found conflicts left
    if other_conflicts and not to_resolve:
        return resolved_versions + resolve_conflicts(other_conflicts[0],
                                                     other_conflicts[1:])
    # if we have a lot of work...
    if other_conflicts and to_resolve:
        # resolve our conflicts first
        return resolved_versions + resolve_conflicts(
            other_conflicts[0], other_conflicts[1:] + to_resolve)
