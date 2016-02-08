# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.db import transaction

from reversion.models import Version
from reversion.revisions import (
    default_revision_manager, revision_context_manager)

from django.contrib import admin
from django.core.urlresolvers import reverse, NoReverseMatch
from django.test import Client

from cms import api

from aldryn_reversion.test_helpers.project.test_app.models import (
    SimpleRegistered, SimpleNoAdmin, SimpleFK, SimpleRequiredFK, BlankFK,
)

from .base import (
    HelperModelsObjectsSetupMixin, CMSRequestBasedMixin, ReversionBaseTestCase,
    get_version_for_object,
)

VERSION_INFO = "{content_type_name} #{object_id_int}: {object_repr}"
PLACEHOLDER_STR = RESOLVABLE_CONFLICT_STR = NON_RESOLVABLE_CONFLICT_STR = (
    VERSION_INFO)
VERSIONS_INFO = {
    'ph': PLACEHOLDER_STR,
    'conflict': RESOLVABLE_CONFLICT_STR,
    'non_resolavable': NON_RESOLVABLE_CONFLICT_STR
}
PLACEHOLDER_INFO = (
    'The following placeholders were deleted and will be restored')
CONFLICT_INFO = 'Please restore required related objects first'
NON_RESOLVABLE_CONFLICT_INFO = (
    'The following conflicts would be recovered automatically'
)
ALL_INFO_MESSAGES = [PLACEHOLDER_INFO, CONFLICT_INFO,
                     NON_RESOLVABLE_CONFLICT_INFO]
REVERT_BUTTON = RECOVER_BUTTON = (
    """<input type="submit" value="Yes, I'm sure" />""")


class AdminUtilsMixin(object):
    def setUp(self):
        super(AdminUtilsMixin, self).setUp()
        admin.autodiscover()
        self.admin_registry = admin.site._registry

    def get_admin_url_for_obj(self, obj, view_name, version=None):
        """
        Build admin view_name url for object.
        """
        opts = obj._meta
        url = reverse(
            'admin:{0}_{1}_{2}'.format(
                opts.app_label,
                obj._meta.model_name,
                view_name),
            args=[obj.pk if version is None else version.pk])
        return url

    def get_admin_instance_for_object(self, obj_or_version):
        """
        Return an admin instance for object or version.object_version.object
        if version was provided instead of object.
        """
        kls = (obj_or_version._meta.model
               if not type(obj_or_version) == Version
               else obj_or_version.content_type.model_class())

        admin_instance = self.admin_registry[kls]
        return admin_instance

    def build_string_args(self, version):
        """
        Prepare dict for building version info the same way it is specified in
        the template. Method is being used to populate prepared raw strings:
        PLACEHOLDER_STR, RESOLVABLE_CONFLICT_STR, NON_RESOLVABLE_CONFLICT_STR
        """
        return {'content_type_name': version.content_type.name.capitalize(),
                'object_id_int': version.object_id_int,
                'object_repr': version.object_repr}


class ReversionRecoverAdminTestCase(AdminUtilsMixin,
                                    CMSRequestBasedMixin,
                                    HelperModelsObjectsSetupMixin,
                                    ReversionBaseTestCase):

    def get_admin_url_for_obj(self, obj, view_name='recover', version=None):
        """
        Build admin view url for object, if view_name is not specified - builds
        url for recover view.
        """
        return super(ReversionRecoverAdminTestCase,
                     self).get_admin_url_for_obj(obj, view_name, version)

    def get_version(self, object_or_version):
        """
        Returns version or latest version for object, if object_or_version is
        object not reversion.models.Version.
        """
        return (object_or_version if type(object_or_version) == Version
                else get_version_for_object(object_or_version))

    def get_recover_view_response(self, obj_or_version, version_id=None,
                                  language='en'):
        """
        Returns result of admin recover_view processing (response) for given
        object (object_or_version).
        If object is a Version - uses version.object_version.object.
        If version_id was not provided - latest available version.id is used.
        """
        if version_id is None:
            version_id = str(self.get_version(obj_or_version).id)
        url = self.get_admin_url_for_obj(self.get_object(obj_or_version))

        request = self.get_su_request(language, url)
        admin_instance = self.get_admin_instance_for_object(obj_or_version)
        return admin_instance.recover_view(request, version_id)

    def post_recover_view_response(self, obj_or_version, language='en',
                                   version_id=None):
        """
        Mock a post request to admin view. Returns result of admin recover_view
        processing (response) for given object (object_or_version).
        If object is a Version - uses version.object_version.object.
        If version_id was not provided - latest available version.id is used.
        """
        if version_id is None:
            version_id = str(self.get_version(obj_or_version).id)
        url = self.get_admin_url_for_obj(self.get_object(obj_or_version))
        request = self.get_su_request(language, url)
        request.method = 'POST'
        admin_instance = self.get_admin_instance_for_object(obj_or_version)
        return admin_instance.recover_view(request, version_id)

    def check_info(self, response, info_string, versions=None):
        """
        Check that response contains info_string message,
        if versions are passed builds version info strings and checks that
        they were rendered. Expects versions to be a dict i.e
        { 'ph': placeholder_versions_list,
          'conflict': conflict_versions_list,
          'non_resolvable': non_resolvable_conflicts_versions_list
        }
        """
        self.assertContains(response, info_string)
        if versions:
            search_for = []
            for msg, versions_list in versions.items():
                version_info = VERSIONS_INFO[msg]
                search_for += [version_info.format(
                    **self.build_string_args(version)
                ) for version in versions_list]

            for info in search_for:
                self.assertContains(response, info)

    def test_recover_view_access(self):
        # test accessible for admin registered objects, should be greated than 4
        # characters, since '/en/' is 4, and actually not raises an exception
        self.assertGreater(
            len(self.get_admin_url_for_obj(self.simple_registered)),
            4)
        # test not accessible for not registered objects
        with self.assertRaises(NoReverseMatch):
            self.get_admin_url_for_obj(self.simple_no_admin)

    def test_recover_view_works_with_simple_objects(self):
        simple_version = get_version_for_object(self.simple_registered)
        self.simple_registered.delete()
        self.assertEqual(SimpleRegistered.objects.count(), 0)

        response = self.get_recover_view_response(simple_version)
        for info in ALL_INFO_MESSAGES:
            self.assertNotContains(response, info)

        # test recover button is accessible for simple object
        self.assertContains(response, RECOVER_BUTTON)
        # test recover is actually recovers object
        response = self.post_recover_view_response(simple_version)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SimpleRegistered.objects.count(), 1)

    def test_recover_warnings_on_conflicts(self):
        # check that there is no warning on conflictable object
        # if there is no conflict
        simple_fk_version = get_version_for_object(self.simple_fk)
        self.simple_fk.delete()
        self.assertEqual(SimpleFK.objects.count(), 0)
        response = self.get_recover_view_response(
            simple_fk_version, version_id=str(simple_fk_version.id))
        for info in ALL_INFO_MESSAGES:
            self.assertNotContains(response, info)
        # check that in this case recover button is accessible
        self.assertContains(response, RECOVER_BUTTON)

        # check that recovered object is actually being restored
        response = self.post_recover_view_response(simple_fk_version)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SimpleFK.objects.count(), 1)

        # make conflict which is solvable by user
        simple_registered_version = get_version_for_object(
            self.simple_registered)
        conflict_url = self.get_admin_url_for_obj(
            self.simple_registered, version=simple_registered_version)
        simple_required_fk_version = get_version_for_object(
            self.simple_required_fk)
        self.simple_registered.delete()
        self.simple_required_fk.delete()
        self.assertEqual(SimpleRegistered.objects.count(), 0)
        self.assertEqual(SimpleRequiredFK.objects.count(), 0)

        # check that there is a link to conflict
        response = self.get_recover_view_response(simple_required_fk_version)
        # check info messages.
        self.check_info(response, CONFLICT_INFO,
                        versions={'conflict': [simple_registered_version]})
        self.assertContains(response, conflict_url)
        # check that there is no recover button
        self.assertNotContains(response, RECOVER_BUTTON)

    # Test that if model has blank/null true conflicts are detected
    def test_recover_warnings_on_conflicts_for_blank_fk(self):
        # check that there is no warning on conflictable object
        # if there is no conflict
        blank_fk_version = get_version_for_object(self.blank_fk)
        self.blank_fk.delete()
        self.assertEqual(BlankFK.objects.count(), 0)
        response = self.get_recover_view_response(
            blank_fk_version, version_id=str(blank_fk_version.id))
        for info in ALL_INFO_MESSAGES:
            self.assertNotContains(response, info)
        # check that in this case recover button is accessible
        self.assertContains(response, RECOVER_BUTTON)

        # check that recovered object is actually being restored
        response = self.post_recover_view_response(blank_fk_version)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(BlankFK.objects.count(), 1)

        # since we have only one object we can do that =)
        self.blank_fk = BlankFK.objects.get()
        # make conflict which is solvable by user
        blank_fk_version = get_version_for_object(self.blank_fk)
        # since there might (or actually is) another revisions, use the same
        # revision as blank_fk_version, otherwise conflict url will mismatch
        simple_registered_version = get_version_for_object(
            self.blank_fk.simple_relation,
            revision_pk=blank_fk_version.revision.pk)
        conflict_url = self.get_admin_url_for_obj(
            self.blank_fk.simple_relation, version=simple_registered_version)
        # delete objects
        self.blank_fk.delete()
        self.assertEqual(BlankFK.objects.count(), 0)
        self.simple_registered.delete()
        self.assertEqual(SimpleRegistered.objects.count(), 0)

        # check that there is a link to conflict
        response = self.get_recover_view_response(blank_fk_version)
        # check info messages.
        self.check_info(response, CONFLICT_INFO,
                        versions={'conflict': [simple_registered_version]})
        self.assertContains(response, conflict_url)
        # check that there is no recover button
        self.assertNotContains(response, RECOVER_BUTTON)

    def test_recover_no_warnings_on_non_recoverable_by_user_conflict(self):
        # check that if there is no conflict - there is no warning

        simple_fk_version = get_version_for_object(self.simple_fk)
        self.simple_fk.delete()
        self.assertEqual(SimpleFK.objects.count(), 0)
        response = self.get_recover_view_response(simple_fk_version)
        for info in ALL_INFO_MESSAGES:
            self.assertNotContains(response, info)

        # check that recover button is accessible
        self.assertContains(response, RECOVER_BUTTON)

        # make conflict
        no_admin_verson = get_version_for_object(self.simple_no_admin)
        self.simple_no_admin.delete()
        # check that there is no conflict warning
        response = self.get_recover_view_response(simple_fk_version)
        self.assertNotContains(response, CONFLICT_INFO)
        self.assertContains(response, NON_RESOLVABLE_CONFLICT_INFO)
        # check that conflict object is listed among objects being recovered
        self.check_info(response, NON_RESOLVABLE_CONFLICT_INFO,
                        versions={'non_resolavable': [no_admin_verson]})
        # check that recover button is accessible
        self.assertContains(response, RECOVER_BUTTON)
        # check recovered objects are actually restored
        response = self.post_recover_view_response(simple_fk_version)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SimpleFK.objects.count(), 1)
        self.assertEqual(SimpleNoAdmin.objects.count(), 1)


class ReversionRevisionAdminTestCase(AdminUtilsMixin,
                                     CMSRequestBasedMixin,
                                     HelperModelsObjectsSetupMixin,
                                     ReversionBaseTestCase):

    def get_admin_url_for_obj(self, obj, view_name, version=None):
        """
        Build admin view_name url for object.
        """
        opts = obj._meta
        url = reverse(
            'admin:{0}_{1}_{2}'.format(
                opts.app_label,
                obj._meta.model_name,
                view_name),
            args=[obj.pk, version.pk])
        return url

    def get_revision_view_response(self, obj, version, language='en'):
        url = self.get_admin_url_for_obj(obj, 'revision', version)
        request = self.get_su_request(language, url)
        admin_instance = self.get_admin_instance_for_object(obj)
        return admin_instance.revision_view(request,
                                            str(obj.pk),
                                            str(version.pk))

    def post_revision_veiw_response(self, obj, version, language='en'):
        url = self.get_admin_url_for_obj(obj, 'revision', version)
        request = self.get_su_request(language, url)
        request.method = 'POST'
        admin_instance = self.get_admin_instance_for_object(obj)
        return admin_instance.revision_view(request,
                                            str(obj.pk),
                                            str(version.pk))

    def test_revision_view_is_accessible(self):
        simple_registered_version = get_version_for_object(
            self.simple_registered)
        response = self.get_revision_view_response(
            self.simple_registered, simple_registered_version)
        for version in simple_registered_version.revision.version_set.all():
            self.assertContains(response, VERSION_INFO.format(
                **self.build_string_args(version)))
        self.assertContains(response, REVERT_BUTTON)

    def test_revision_view_reverts_object_to_selected_state(self):
        initial_position = self.simple_registered.position
        new_position = 99
        self.create_revision(self.simple_registered, position=new_position)
        self.assertNotEqual(initial_position, self.simple_registered.position)
        prev_version = default_revision_manager.get_for_object(
            self.simple_registered)[1]
        response = self.post_revision_veiw_response(
            self.simple_registered, prev_version)
        self.assertEqual(response.status_code, 302)
        self.simple_registered = SimpleRegistered.objects.get(
            pk=self.simple_registered.pk)
        self.assertEquals(self.simple_registered.position, initial_position)

    def test_admin_create_obj_view(self):
        """Test that admin create view works and actually creates an object"""
        obj_count = SimpleRegistered.objects.count()
        obj = SimpleRegistered.objects.first()
        url = reverse(
            'admin:{0}_{1}_{2}'.format(
                obj._meta.app_label,
                obj._meta.model_name,
                'add'))
        client = Client()
        # TODO: we can replace this with force_login() on Django 1.9+
        client.login(username=self.super_user.username,
                     password=self.super_user_password)
        position = '777'
        response = client.post(url, data={'position': position}, follow=True)
        self.assertEqual(obj_count, SimpleRegistered.objects.count() - 1)
        self.assertContains(response, position)


class AdminUtilsMethodsTestCase(AdminUtilsMixin,
                                CMSRequestBasedMixin,
                                HelperModelsObjectsSetupMixin,
                                ReversionBaseTestCase):

    def test_create_aldryn_revision(self):
        # would be used to get admin instance
        with_placeholder_version = get_version_for_object(
            self.with_placeholder)

        admin_instance = self.get_admin_instance_for_object(
            with_placeholder_version)
        plugin = api.add_plugin(self.with_placeholder.content,
                                'TextPlugin', language='en')
        plugin.body = 'Initial text'
        plugin.save()
        # ensure there was no versions for plugin before
        self.assertEqual(
            default_revision_manager.get_for_object(plugin).count(), 0)
        with transaction.atomic():
            with revision_context_manager.create_revision():
                admin_instance._create_aldryn_revision(
                    plugin.placeholder,
                    comment='New aldryn revision with initial plugin')
        # ensure there is at least one version after create aldryn revision
        self. assertEqual(
            default_revision_manager.get_for_object(plugin).count(), 1)
        new_plugin_text = 'test plugin content was changed'
        plugin.body = new_plugin_text
        plugin.save()
        with transaction.atomic():
            with revision_context_manager.create_revision():
                admin_instance._create_aldryn_revision(
                    plugin.placeholder,
                    comment='New aldryn revision with initial plugin')

        # ensure there is at least one version after create aldryn revision
        self. assertEqual(
            default_revision_manager.get_for_object(plugin).count(), 2)
        latest_plugin = plugin._meta.model.objects.get(pk=plugin.pk)

        # ensure text is latest
        self.assertEqual(latest_plugin.body, new_plugin_text)
        # ensure text is initial if reverted to previous revision
        prev_version = default_revision_manager.get_for_object(
            self.with_placeholder)[1]
        prev_version.revision.revert()
        # refresh from db
        latest_plugin = plugin._meta.model.objects.get(pk=plugin.pk)
        # ensure plugin text was chagned. Note however that there might be
        # different paths to ensure that text is chagned for CMSPlugin
        # This only checks that plugin content (which is text plugin not the cms
        # is reverted, so be careful.
        self.assertEqual(latest_plugin.body, 'Initial text')
