# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from reversion.revisions import default_revision_manager
from cms.models import Placeholder

from aldryn_reversion.test_helpers.project.test_app.models import (
    SimpleNoAdmin, SimpleFK, WithPlaceholder, WithTranslations,
)

from ..forms import RecoverObjectWithTranslationForm
from ..utils import (
    RecursiveRevisionConflictResolver, get_deleted_placeholders_for_object,
)

from .base import (
    ReversionBaseTestCase, HelperModelsObjectsSetupMixin,
    get_version_for_object
)


class FormsTestCase(HelperModelsObjectsSetupMixin, ReversionBaseTestCase):
    form_class = RecoverObjectWithTranslationForm

    def build_form_kwargs(self, obj):
        version = get_version_for_object(obj)
        return {
            'revision': version.revision,
            'obj': obj,
            'version': version,
            'resolve_conflicts': [],
            'placeholders': [],
        }

    def build_unbound_form(self, args_dict):
        """
        Build a self.form_class unbound form, args_dict - keyword arguments
        that will be passed to form class __init__.
        """
        return self.form_class(**args_dict)

    def build_bound_form(self, args_dict):
        """
        Build a self.form_class bound form by also providing `data` kw argument,
        to form_class __init__ method to bypass django checks.
        Expects args_dict to be keyword arguments that will be passed to
        form class __init__.
        """
        dummy = {'dummy': 1}
        return self.form_class(data=dummy, **args_dict)

    def compare_form_attrs(self, form, form_kwargs):
        """
        Check that form attributes equal to form_kwargs.
        tries to get attributes based on form_kwargs keys and compare to
        form_kwargs values. if none or miss match - returns dict of
        {attribute name: attribute value}
        """
        not_equal = {}
        for arg_name, value in form_kwargs.items():
            found = False
            form_arg = getattr(form, arg_name, None)
            if type(form_arg) == list:
                arg_not_equal = [item for item in form_arg
                                 if item not in form_kwargs[arg_name]]
                # if there is less or more items consider lists not equal
                if arg_not_equal or len(form_arg) > len(form_kwargs[arg_name]):
                    found = True
            elif form_arg is None or form_arg != form_kwargs[arg_name]:
                arg_not_equal = form_arg
                found = True
            if found:
                not_equal[arg_name] = arg_not_equal
        return not_equal

    def test_recover_form_init(self):
        # test with not translatable object, should not contain translations
        # field
        form_simple_kwargs = self.build_form_kwargs(self.simple_no_admin)
        form_simple = self.build_unbound_form(form_simple_kwargs)
        self.assertNotIn('translations', form_simple.fields.keys())

        # test with translatable object, should contain translations field
        form_translated_kwargs = self.build_form_kwargs(self.with_translation)
        form_translated = self.build_unbound_form(form_translated_kwargs)
        self.assertIn('translations', form_translated.fields.keys())

        # test that form has correct in memory attrs which are (atm):
        # * revision,
        # * obj (object which would be recovered)
        # * version (object version)
        # * resolve_conflicts (list of versions to recover)
        # * placeholders (list of versions to recover)
        # Also test that creating second form doesn't affect first form
        # in-memory attributes and vice versa.
        not_equal = self.compare_form_attrs(form_simple, form_simple_kwargs)
        message = 'Args not found or missmatch for {0} object {1}'
        self.assertEqual(len(not_equal), 0, msg=message.format(
            'simple_no_admin', not_equal))
        not_equal = self.compare_form_attrs(form_translated,
                                            form_translated_kwargs)
        self.assertEqual(len(not_equal), 0, msg=message.format(
            'with_translation', not_equal))

    def test_recover_form_clean(self):
        # test with no conflicts, should validate fine
        form_simple_kwargs = self.build_form_kwargs(self.simple_no_admin)
        # form validation doesn't triggers if form is not bound, so
        # we need to pass dummy data so it would be considered as bound
        # Should not be the case in real life because of request.POST

        form_simple = self.build_bound_form(form_simple_kwargs)
        self.assertTrue(form_simple.is_valid())

        # test with not resolved conflicts - should rise validation error
        simple_no_admin_version = default_revision_manager.get_for_object(
            self.simple_no_admin)[0]
        self.simple_no_admin.delete()
        self.assertEqual(SimpleNoAdmin.objects.count(), 0)
        self.assertEqual(SimpleFK.objects.count(), 0)
        simple_fk_kwargs = self.build_form_kwargs(self.simple_fk)
        form_simple_fk_with_conflicts = self.build_bound_form(simple_fk_kwargs)
        self.assertFalse(form_simple_fk_with_conflicts.is_valid())
        self.assertEqual(
            len(form_simple_fk_with_conflicts.non_field_errors()), 1)
        self.assertEqual(form_simple_fk_with_conflicts.non_field_errors()[0],
                         'Cannot restore object, there are conflicts!')

        # test with conflicts that were resolved by utility
        # RecursiveRevisionConflictResolver, and result were passed to form
        # init, should validate fine
        simple_fk_resolved_conflicts = RecursiveRevisionConflictResolver(
            simple_fk_kwargs['version']).resolve()
        simple_fk_kwargs['resolve_conflicts'] = simple_fk_resolved_conflicts
        form_simple_fk_resolved = self.build_bound_form(simple_fk_kwargs)
        self.assertTrue(form_simple_fk_resolved.is_valid())

        # test with conflicts that were resolved, and passed to form init,
        # but then something more was corrupted (new conflicts) should raise
        simple_no_admin_version.revert()
        partially_resolved = RecursiveRevisionConflictResolver(
            simple_fk_kwargs['version']).resolve()
        simple_fk_kwargs['resolve_conflicts'] = partially_resolved
        form_simple_fk_resolved = self.build_bound_form(simple_fk_kwargs)
        # delete object which was not resolved by resolver
        SimpleNoAdmin.objects.all()[0].delete()
        self.assertEqual(SimpleNoAdmin.objects.count(), 0)
        self.assertFalse(form_simple_fk_resolved.is_valid())

    def test_recover_form_save(self):
        # test reverts object_version (no extras, simple object with
        # no translations, placeholders or fks
        form_simple_kwargs = self.build_form_kwargs(self.simple_no_admin)
        self.simple_no_admin.delete()
        self.assertEqual(SimpleNoAdmin.objects.count(), 0)
        form_simple = self.build_bound_form(form_simple_kwargs)
        self.assertTrue(form_simple.is_valid())
        form_simple.save()
        self.assertEqual(SimpleNoAdmin.objects.count(), 1)

        # test reverts object and deleted placeholders
        with_placeholder_version = default_revision_manager.get_for_object(
            self.with_placeholder)[0]
        placeholder_pk = self.with_placeholder.content.pk
        self.with_placeholder.content.delete()
        # check that placeholder was actually deleted.
        self.assertEqual(
            Placeholder.objects.filter(pk=placeholder_pk).count(), 0)

        placeholder_versions = get_deleted_placeholders_for_object(
            self.with_placeholder, with_placeholder_version.revision)
        form_with_placeholders_kwargs = self.build_form_kwargs(
            self.with_placeholder)
        self.with_placeholder.delete()
        self.assertEqual(WithPlaceholder.objects.count(), 0)

        form_with_placeholders_kwargs['placeholders'] = placeholder_versions
        form_with_placeholder = self.build_bound_form(
            form_with_placeholders_kwargs)
        self.assertTrue(form_with_placeholder.is_valid())
        form_with_placeholder.save()
        self.assertEqual(WithPlaceholder.objects.count(), 1)
        # check that placeholder was restored
        self.assertEqual(
            Placeholder.objects.filter(pk=placeholder_pk).count(), 1)

        # test reverts object and translations
        form_translated_kwargs = self.build_form_kwargs(self.with_translation)

        self.with_translation.delete()
        self.assertEqual(WithTranslations.objects.count(), 0)
        self.assertEqual(
            self.with_translation.translations.count(), 0)
        form_with_translation = self.build_unbound_form(form_translated_kwargs)

        translations_pks = [tr[0] for tr in
                            form_with_translation.fields[
                                'translations'].choices]
        form_with_translation = self.form_class(
            {'translations': translations_pks}, **form_translated_kwargs)
        self.assertTrue(form_with_translation.is_valid())
        form_with_translation.save()

        self.assertEqual(WithTranslations.objects.count(), 1)
        self.assertEqual(WithTranslations.objects.get().translations.count(), 2)
        self.assertEqual(self.with_translation.description,
                         WithTranslations.objects.get().description)

        # test reverts object and conflicts
        simple_fk_kwargs = self.build_form_kwargs(self.simple_fk)
        SimpleNoAdmin.objects.get().delete()
        self.assertEqual(SimpleNoAdmin.objects.count(), 0)
        self.assertEqual(SimpleFK.objects.count(), 0)
        simple_fk_resolved_conflicts = RecursiveRevisionConflictResolver(
            simple_fk_kwargs['version']).resolve()
        simple_fk_kwargs['resolve_conflicts'] = simple_fk_resolved_conflicts
        form_simple_fk_resolved = self.build_bound_form(simple_fk_kwargs)
        self.assertTrue(form_simple_fk_resolved.is_valid())
        form_simple_fk_resolved.save()
        self.assertEqual(SimpleFK.objects.count(), 1)
        self.assertEqual(SimpleNoAdmin.objects.count(), 1)
        self.assertEqual(self.simple_fk.simple_relation,
                         SimpleFK.objects.get().simple_relation)
