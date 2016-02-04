# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from reversion.models import Version
from reversion.revisions import default_revision_manager
from cms.models import Placeholder

from ..utils import (
    object_is_translation, object_has_placeholders,
    get_placeholder_fields_names, get_fk_models,
    get_translations_versions_for_object, get_deleted_objects_versions,
    get_conflict_fks_versions, get_deleted_placeholders,
    get_deleted_placeholders_for_object,
    RecursiveRevisionConflictResolver,
)

from .base import (
    ReversionBaseTestCase, HelperModelsObjectsSetupMixin,
    get_version_for_object
)
from aldryn_reversion.test_helpers.project.test_app.models import (
    SimpleNoAdmin, SimpleRegistered, WithPlaceholder,
    SimpleFK, BlankFK, ComplexOneFK, MultiLevelFK,
)


class UtilsTestCase(HelperModelsObjectsSetupMixin, ReversionBaseTestCase):

    def test_object_is_translation(self):
        # false for original object
        self.assertFalse(object_is_translation(self.with_translation))
        # true for translation object
        translation = self.with_translation.translations.all()[0]
        self.assertTrue(object_is_translation(translation))

    def test_object_has_placeholders(self):
        self.assertFalse(object_has_placeholders(self.with_translation))
        self.assertTrue(object_has_placeholders(self.with_placeholder))

    def test_get_placeholder_fields_names(self):
        placeholder_name = 'content'
        result = get_placeholder_fields_names(self.with_placeholder)
        self.assertEqual(len(result), 1)
        self.assertIn(placeholder_name, result)

        # check that calling function for second time doesn't changes result
        result = get_placeholder_fields_names(self.with_placeholder)
        self.assertEqual(len(result), 1)

    def test_get_fk_models(self):
        # all fk's, blankness in models shouldn't affect the result
        result_all = get_fk_models(self.simple_fk)
        result_models = [relation['model'] for relation in result_all]
        self.assertEqual(len(result_all), 1)
        self.assertIn(SimpleNoAdmin, result_models)

        result_all = get_fk_models(self.blank_fk)
        result_models = [relation['model'] for relation in result_all]
        self.assertEqual(len(result_all), 1)
        self.assertIn(SimpleRegistered, result_models)

        # required fk's
        result_required = get_fk_models(self.simple_fk, blank=False)
        result_required_models_only = [relation['model']
                                       for relation in result_required]
        self.assertEqual(len(result_required), 1)
        self.assertIn(SimpleNoAdmin, result_required_models_only)

        result_required = get_fk_models(self.blank_fk, blank=False)
        self.assertEqual(len(result_required), 0)

        # not required fk's
        result_not_required = get_fk_models(self.blank_fk, blank=True)
        result_not_required_models = [relation['model']
                                      for relation in result_not_required]
        self.assertEqual(len(result_not_required), 1)
        self.assertIn(SimpleRegistered, result_not_required_models)

        result_not_required = get_fk_models(self.simple_fk, blank=True)
        self.assertEqual(len(result_not_required), 0)

    def test_get_translations_versions_for_object(self):
        # check that object has 2 translation already
        self.assertEqual(self.with_translation.translations.count(), 2)
        # get_for_object returns latest version first.
        version_2 = default_revision_manager.get_for_object(
            self.with_translation)[0]
        version_1 = default_revision_manager.get_for_object(
            self.with_translation)[1]
        revision_2 = version_2.revision
        revision_1 = version_1.revision
        # compare count of translations from latest revision to actual count
        result_revision_2 = get_translations_versions_for_object(
            self.with_translation, revision_2)
        result_revision_1 = get_translations_versions_for_object(
            self.with_translation, revision_1)

        self.assertEqual(len(result_revision_2), 2)
        self.assertEqual(len(result_revision_1), 1)

        # test with providing versions explicitly, should respect versions
        # over revision
        exclude_en_pks = default_revision_manager.get_for_object(
            self.with_translation.translations.filter(
                language_code='en').get()).values_list('pk', flat=True)
        versions = revision_2.version_set.all().exclude(
            pk__in=exclude_en_pks)
        # check that we have versions (should be object and german translation)
        self.assertEqual(len(versions), 2)
        result_versions = get_translations_versions_for_object(
            self.with_translation, revision_1, versions=versions)
        self.assertEqual(len(result_versions), 1)

    def test_get_deleted_objects_versions(self):
        blank_fk_version = default_revision_manager.get_for_object(
            self.blank_fk)[0]
        blank_fk_pk = self.blank_fk.pk
        # ensure that returns nothing for not deleted objects
        result = get_deleted_objects_versions(
            blank_fk_version.revision.version_set.all())
        self.assertEqual(len(result), 0)

        # delete and ensure that object was deleted.
        self.blank_fk.delete()
        self.assertEqual(
            BlankFK.objects.filter(pk=blank_fk_pk).count(), 0)
        # test against deleted object
        result = get_deleted_objects_versions(
            blank_fk_version.revision.version_set.all())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].object_id_int, blank_fk_pk)

        # test with mixing 2 deleted object Versions
        simple_fk_version = default_revision_manager.get_for_object(
            self.simple_fk)[0]
        simple_fk_pk = self.simple_fk.pk
        self.simple_fk.delete()
        self.assertEqual(SimpleFK.objects.filter(pk=simple_fk_pk).count(), 0)
        # construct versions with this two objects and test
        blank_fk_versions_pks = [version.pk for version in
                                 blank_fk_version.revision.version_set.all()]
        simple_fk_versions_pks = [version.pk for version in
                                  simple_fk_version.revision.version_set.all()]
        both_obj_versions_pks = blank_fk_versions_pks + simple_fk_versions_pks
        custom_versions = Version.objects.filter(pk__in=both_obj_versions_pks)
        result = get_deleted_objects_versions(custom_versions)
        self.assertEqual(len(result), 2)

    def test_get_conflict_fks_versions_with_simple_models(self):
        # test with object that has no relations
        simple_no_admin_version = default_revision_manager.get_for_object(
            self.simple_registered)[0]
        result = get_conflict_fks_versions(
            self.simple_registered, simple_no_admin_version,
            simple_no_admin_version.revision)
        self.assertEqual(len(result), 0)

        # test with object that has no conflicts
        simple_fk_version = default_revision_manager.get_for_object(
            self.simple_fk)[0]
        result = get_conflict_fks_versions(
            self.simple_fk, simple_fk_version, simple_fk_version.revision)
        self.assertEqual(len(result), 0)

        # test with object that has conflicts
        self.simple_fk.delete()
        self.simple_no_admin.delete()
        result = get_conflict_fks_versions(
            self.simple_fk, simple_fk_version, simple_fk_version.revision)
        self.assertEqual(len(result), 1)

        # check that exclude excludes by excluding previous result version
        result = get_conflict_fks_versions(
            self.simple_fk, simple_fk_version, simple_fk_version.revision,
            exclude={'pk': result[0].pk})
        self.assertEqual(len(result), 0)

    def test_get_conflict_fks_versions_with_blank_fk_model(self):
        # test with no conflict
        bank_fk_version = default_revision_manager.get_for_object(
            self.blank_fk)[0]
        result = get_conflict_fks_versions(
            self.blank_fk, bank_fk_version, bank_fk_version.revision)
        self.assertEqual(len(result), 0)

        # test with conflict,
        self.blank_fk.delete()
        self.simple_registered.delete()
        result = get_conflict_fks_versions(
            self.blank_fk, bank_fk_version, bank_fk_version.revision)
        self.assertEqual(len(result), 1)

    def test_get_conflict_fks_versions_with_blank_fk_no_fk(self):
        # test with new blank fk that has no relations, should not have
        # conflicts after delete.
        new_blank_fk = self.create_with_revision(BlankFK)
        new_blank_fk_version = default_revision_manager.get_for_object(
            new_blank_fk)[0]
        result = get_conflict_fks_versions(
            new_blank_fk, new_blank_fk_version, new_blank_fk_version.revision)
        self.assertEqual(len(result), 0)

    def test_get_deleted_placeholders(self):
        with_placeholder_version = default_revision_manager.get_for_object(
            self.with_placeholder)[0]
        # test returns nothing if there are no deleted placeholders
        result = get_deleted_placeholders(with_placeholder_version.revision)
        self.assertEqual(len(result), 0)

        # delete placeholder
        placeholder_pk = self.with_placeholder.content.pk
        self.with_placeholder.content.delete()
        # check that placeholder was actually deleted.
        self.assertEqual(self.with_placeholder._meta.model.objects.filter(
            pk=placeholder_pk).count(), 0)

        result = get_deleted_placeholders(with_placeholder_version.revision)
        self.assertEqual(len(result), 1)

        # test with revision that has more then one deleted placeholder
        # (misc objects)
        complex_one_fk_version = default_revision_manager.get_for_object(
            self.complex_one_fk)[0]
        other_placeholder_pk = self.complex_one_fk.complex_content.pk
        self.complex_one_fk.complex_content.delete()
        self.assertEqual(self.with_placeholder._meta.model.objects.filter(
            pk__in=[placeholder_pk, other_placeholder_pk]).count(), 0)
        result = get_deleted_placeholders(complex_one_fk_version.revision)
        self.assertEqual(len(result), 2)

    def test_get_deleted_placeholders_for_object(self):
        # test that it not fails with object that has no placeholders
        simple_no_admin_version = default_revision_manager.get_for_object(
            self.simple_no_admin)[0]
        result = get_deleted_placeholders_for_object(
            self.with_placeholder, simple_no_admin_version.revision)
        self.assertEqual(len(result), 0)

        # test if no placeholders were deleted
        with_placeholder_version = default_revision_manager.get_for_object(
            self.with_placeholder)[0]
        result = get_deleted_placeholders_for_object(
            self.with_placeholder, with_placeholder_version.revision)
        self.assertEqual(len(result), 0)

        # test if placeholder was deleted for this object
        # delete placeholder
        placeholder_pk = self.with_placeholder.content.pk
        self.with_placeholder.content.delete()
        # check that placeholder was actually deleted.
        self.assertEqual(self.with_placeholder._meta.model.objects.filter(
            pk=placeholder_pk).count(), 0)

        result = get_deleted_placeholders_for_object(
            self.with_placeholder, with_placeholder_version.revision)
        self.assertEqual(len(result), 1)

        # test if placeholder was deleted for not related object (no result)
        complex_one_fk_version = default_revision_manager.get_for_object(
            self.complex_one_fk)[0]
        other_placeholder_pk = self.complex_one_fk.complex_content.pk
        self.complex_one_fk.complex_content.delete()
        self.assertEqual(self.with_placeholder._meta.model.objects.filter(
            pk__in=[placeholder_pk, other_placeholder_pk]).count(), 0)

        result = get_deleted_placeholders_for_object(
            self.with_placeholder, with_placeholder_version.revision)
        self.assertEqual(len(result), 1)

        result = get_deleted_placeholders_for_object(
            self.complex_one_fk, complex_one_fk_version.revision)
        self.assertEqual(len(result), 1)

    def test_recursive_resolver_resolve_conflicts(self):
        # test with no conflicts
        #  * no translations, placeholders, fks
        simple_no_adm_version = get_version_for_object(
            self.simple_registered)
        result = RecursiveRevisionConflictResolver(
            simple_no_adm_version).resolve()
        self.assertEqual(len(result), 1)

        #  * with translations
        with_trans_version = get_version_for_object(
            self.with_translation)
        result = RecursiveRevisionConflictResolver(with_trans_version).resolve()
        # one version for the object itself, and 2 for translations
        self.assertEqual(len(result), 3)

        #  * with placeholders
        with_ph_version = get_version_for_object(self.with_placeholder)
        result = RecursiveRevisionConflictResolver(with_ph_version).resolve()
        self.assertEqual(len(result), 1)

        #  * with fks
        simple_fk_version = get_version_for_object(self.simple_fk)
        result = RecursiveRevisionConflictResolver(simple_fk_version).resolve()
        self.assertEqual(len(result), 1)

        #  * with all of that
        complex_fk_version = get_version_for_object(self.complex_one_fk)
        result = RecursiveRevisionConflictResolver(complex_fk_version).resolve()
        # one version for the object itself, and 2 for translations
        self.assertEqual(len(result), 3)

        # test with conflicts
        #  * with simple object
        self.simple_no_admin.delete()
        self.assertEqual(SimpleNoAdmin.objects.count(), 0)
        self.assertEqual(SimpleFK.objects.count(), 0)
        result = RecursiveRevisionConflictResolver(simple_fk_version).resolve()
        # one for simple_fk one for simple_fk's relation to simple_no_admin
        self.assertEqual(len(result), 2)

        #  * with translations,
        #  * with placeholders,
        #  * with FKs
        with_ph_ph_pk = self.with_placeholder.content.pk
        complex_fk_ph_pk = self.complex_one_fk.complex_content.pk
        self.with_placeholder.content.delete()
        self.complex_one_fk.complex_content.delete()
        self.assertEqual(Placeholder.objects.filter(
            pk__in=[with_ph_ph_pk, complex_fk_ph_pk]).count(), 0)

        self.with_placeholder.delete()
        self.assertEqual(WithPlaceholder.objects.count(), 0)
        self.assertEqual(ComplexOneFK.objects.count(), 0)
        result = RecursiveRevisionConflictResolver(complex_fk_version).resolve()
        # 2 for translations, 2 for placeholders, 2 for deleted objects.
        self.assertEqual(len(result), 6)

        # test with version and prepared to resolve.
        # for second and third if clauses.
        self.assertEqual(MultiLevelFK.objects.count(), 0)
        multi_level_fk_version = get_version_for_object(
            self.multi_level_fk)
        result = RecursiveRevisionConflictResolver(
            multi_level_fk_version, [simple_fk_version]).resolve()
        # expecting:
        # [<Version: MultiLevelFK object>, <Version: ComplexOneFK object>,
        # <Version: Complex Content>, <Version: English>, <Version: German>,
        # <Version: WithPlaceholder object>, <Version: Helper model Content>,
        # <Version: SimpleFK object>, <Version: SimpleNoAdmin object>]
        self.assertEqual(len(result), 9)
        # test with duplicates in to_resolve. use results from
        # resolving_conflicts for one of the dependencies.
        result = RecursiveRevisionConflictResolver(
            multi_level_fk_version,
            RecursiveRevisionConflictResolver(simple_fk_version).resolve()
        ).resolve()
        self.assertEqual(len(result), 9)
