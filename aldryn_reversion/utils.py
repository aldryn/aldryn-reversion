from django.contrib.contenttypes.models import ContentType
from django.db.models.fields.related import ForeignKey


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
        versions.exclude(**exclude)
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