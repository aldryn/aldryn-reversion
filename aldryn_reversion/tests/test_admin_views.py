# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from reversion.models import Version

from django.contrib import admin
from django.core.urlresolvers import reverse, NoReverseMatch

from aldryn_reversion.test_helpers.test_app.models import (
    SimpleRegistered,
)

from .base import (
    HelperModelsObjectsSetupMixin, CMSRequersBasedMixin, ReversionBaseTestCase,
    get_latest_version_for_object,
)


PLACEHOLDER_STR = RESOLVABLE_CONFLICT_STR = NON_RESOLVABLE_CONFLICT_STR = (
    "<li>{content_type_name} #{object_id_int}: {object_repr}</li>")
PLACEHOLDER_INFO = (
    'The following placeholders were deleted and will be restored')
CONFLICT_INFO = 'Please restore required related objects first'
NON_RESOLVABLE_CONFLICT_INFO = (
    'The following conflicts would be recovered automatically'
)
ALL_INFO_MESSAGES = [PLACEHOLDER_INFO, CONFLICT_INFO,
                     NON_RESOLVABLE_CONFLICT_INFO]
RECOVER_BUTTON = """<input type="submit" value="Yes, I'm sure" />"""


class AdminUtilsMixin(object):
    def setUp(self):
        super(AdminUtilsMixin, self).setUp()
        admin.autodiscover()
        self.admin_registry = admin.site._registry

    def get_admin_url_for_obj(self, obj, view_name):
        """
        Build admin view_name url for object.
        """
        opts = obj._meta
        url = reverse(
            'admin:{0}_{1}_{2}'.format(
                opts.app_label,
                obj._meta.model_name,
                view_name),
            args=[obj.pk])
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


class ReversionRecoverAdminTestCase(AdminUtilsMixin,
                                    CMSRequersBasedMixin,
                                    HelperModelsObjectsSetupMixin,
                                    ReversionBaseTestCase):

    def get_admin_url_for_obj(self, obj, view_name='recover'):
        """
        Build admin view url for object, if view_name is not specified - builds
        url for recover view.
        """
        return super(ReversionRecoverAdminTestCase,
                     self).get_admin_url_for_obj(obj, view_name)

    def build_string_args(self, version):
        """
        Prepare dict for building version info the same way it is specified in
        the template. Method is being used to populate prepared raw strings:
        PLACEHOLDER_STR, RESOLVABLE_CONFLICT_STR, NON_RESOLVABLE_CONFLICT_STR
        """
        return {'content_type_name': version.content_type.name.capitalize(),
                'object_id_int': version.object_id_int,
                'object_repr': version.object_repr}

    def get_version(self, object_or_version):
        """
        Returns version or latest version for object, if object_or_version is
        object not reversion.models.Version.
        """
        return (object_or_version if type(object_or_version) == Version
                else get_latest_version_for_object(object_or_version))

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
        Mock a post request to admin view. Returns result ofadmin recover_view
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
        they were rendered.
        """
        self.assertContains(response, info_string)
        if versions:
            search_for = [
                PLACEHOLDER_STR.format(self.build_string_args(version))
                for version in versions]
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
        simple_version = get_latest_version_for_object(self.simple_registered)
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

        # check that in this case recover button is accessible
        # check that recovered object is actually being restored

        # make conflict whcih is solvable by user
        # check that there is a link to conflict
        # check that there is no recover button
        pass

    def test_recover_no_warnings_on_non_recoverable_by_user_conflict(self):
        # check that if there is no conflict - there is no warning
        # check that recover button is accessible

        # make conflict
        # check that thre is no conflict warning
        # check that conflict object is listed among objects being recovered
        # check that recover button is accessible
        # check recovered objects are actually restored
        pass