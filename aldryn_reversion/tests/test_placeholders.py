# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from distutils.version import LooseVersion
import sys
import json

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.http.request import QueryDict
from django.utils.encoding import force_text
from django.utils.http import urlencode

from reversion.models import Version, Revision

import cms
from cms.api import create_page, add_plugin
from cms.models import Placeholder, Page, StaticPlaceholder

from aldryn_reversion.test_helpers.project.test_app.models import (
    WithPlaceholder,
)

from .base import (
    HelperModelsObjectsSetupMixin,
    CMSRequestBasedMixin,
    ReversionBaseTestCase,
)

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

# CMS 3.2.1 introduced several fixes for reversions.
# We count on these fixes in some tests.
CMS_3_2_1 = LooseVersion(cms.__version__) >= LooseVersion('3.2.1')
CMS_3_3 = LooseVersion(cms.__version__) >= LooseVersion('3.3')


class ReversionRevisionAdminTestCase(CMSRequestBasedMixin,
                                     HelperModelsObjectsSetupMixin,
                                     ReversionBaseTestCase):

    def get_post_request(self, data=None):
        return self.get_su_request(post_data=data)

    def get_example_admin(self):
        admin.autodiscover()
        return admin.site._registry[WithPlaceholder]

    def get_page_admin(self):
        admin.autodiscover()
        return admin.site._registry[Page]

    def get_staticplaceholder_admin(self):
        admin.autodiscover()
        return admin.site._registry[StaticPlaceholder]

    def get_placeholder_c_type(self):
        return ContentType.objects.get_for_model(Placeholder)

    def get_placeholder_versions(self):
        placeholder_c_type = self.get_placeholder_c_type()
        return Version.objects.filter(content_type=placeholder_c_type)

    def get_plugin_id_from_response(self, response, path):
        # Expects response to be a JSON response
        # with a structure like so:
        # {'path.1': {
        #   'path.2': '/en/admin/app/example1/edit-plugin/3/'}
        # }
        # path is used to access nested keys

        data = json.loads(response.content.decode('utf-8'))
        keys = path.split('.')

        for key in keys:
            data = data[key]
        return data.split('/')[-2]

    def move_a_copy(self, admin, placeholder_id, plugin_id):
        request = self.get_post_request({
            'placeholder_id': placeholder_id,
            'plugin_id': plugin_id,
            'plugin_order': ['__COPY__'],
            'move_a_copy': 'true',
        })
        return admin.move_plugin(request)

    def test_revision_on_placeholder_clear(self):
        placeholder_versions = self.get_placeholder_versions()

        example = WithPlaceholder.objects.create()
        m_pl = example.content
        m_pl_admin = self.get_example_admin()
        m_pl_versions = placeholder_versions.filter(object_id_int=m_pl.pk)
        m_pl_versions_initial_count = m_pl_versions.count()
        m_pl_revisions = Revision.objects.filter(version__in=m_pl_versions)

        data = {
            'placeholder': m_pl,
            'plugin_type': 'TextPlugin',
            'language': 'en',
        }

        # Add plugin to manual placeholder
        add_plugin(**data)

        # assert there's only one plugin in placeholder
        self.assertEqual(m_pl.cmsplugin_set.count(), 1)

        # Clear the placeholder
        request = self.get_post_request(data={'post': 'yes'})
        m_pl_admin.clear_placeholder(request, m_pl.pk)

        # assert placeholder has no plugins
        self.assertEqual(m_pl.cmsplugin_set.count(), 0)

        # assert a new version for the native placeholder has been created
        self.assertEqual(
            m_pl_versions.count(),
            m_pl_versions_initial_count + 1,
        )

        # assert revision comment was set correctly
        self.assertEqual(
            m_pl_revisions.latest('pk').comment,
            'All plugins in the placeholder "%s" '
            'were deleted.' % force_text(m_pl),
        )

    @unittest.skipUnless(CMS_3_2_1, "CMS 3.2.1+ fixed reversion support.")
    def test_revision_on_plugin_move(self):
        from cms.plugin_pool import plugin_pool

        # Begin rant
        # The code below is a great example of why limiting to 80
        # characters is a bad idea.
        # The variable names are cryptic without any context or guide.
        # End rant

        pl_versions = self.get_placeholder_versions()

        TextPluginModel = plugin_pool.get_plugin('TextPlugin').model
        text_plugin_c_type = ContentType.objects.get_for_model(TextPluginModel)

        # three placeholder types
        # native - native CMS placeholder (created using a placeholder tag)
        # manual - Manual placeholder (created using a PlaceholderField)
        # static - Static placeholder (created using the staticplaceholder tag)

        n_pl_page = create_page('test page', 'simple.html', u'en')
        n_pl = n_pl_page.placeholders.get(slot='content_1')
        n_pl_pk = n_pl.pk
        n_pl_admin = self.get_page_admin()
        n_pl_versions = pl_versions.filter(object_id_int=n_pl_pk)
        n_pl_versions_initial_count = n_pl_versions.count()
        n_pl_revisions = Revision.objects.filter(version__in=n_pl_versions)

        example = WithPlaceholder.objects.create()
        m_pl = example.content
        m_pl_admin = self.get_example_admin()
        m_pl_versions = pl_versions.filter(object_id_int=m_pl.pk)
        m_pl_versions_initial_count = m_pl_versions.count()
        m_pl_revisions = Revision.objects.filter(version__in=m_pl_versions)

        static_placeholder_obj = StaticPlaceholder.objects.create(
            name='static',
            code='static',
            site_id=1,
        )
        static_placeholder = static_placeholder_obj.draft
        static_placeholder_admin = self.get_staticplaceholder_admin()

        data = {
            'placeholder': n_pl,
            'plugin_type': 'TextPlugin',
            'language': 'en',
        }

        # Add plugin to native placeholder
        text_plugin = add_plugin(**data)
        text_plugin_pk = text_plugin.pk
        text_plugin_versions = Version.objects.filter(
            content_type=text_plugin_c_type,
            object_id_int=text_plugin_pk,
        )
        text_plugin_versions_initial_count = text_plugin_versions.count()

        # move plugin to manual placeholder
        request = self.get_post_request({
            'placeholder_id': m_pl.pk,
            'plugin_id': text_plugin_pk,
        })
        response = n_pl_admin.move_plugin(request)
        self.assertEqual(response.status_code, 200)

        # assert a new version for the native placeholder has been created
        self.assertEqual(
            n_pl_versions.count(),
            n_pl_versions_initial_count + 1,
        )

        # assert revision comment was set correctly
        self.assertEqual(
            n_pl_revisions.latest('pk').comment,
            'Moved plugins to %s' % force_text(m_pl),
        )

        # assert a new version for the manual placeholder has been created
        self.assertEqual(
            m_pl_versions.count(),
            m_pl_versions_initial_count + 1,
        )

        # assert revision comment was set correctly
        self.assertEqual(
            m_pl_revisions.latest('pk').comment,
            'Moved plugins to %s' % force_text(m_pl),
        )

        # assert a new version for the text plugin has been created
        self.assertEqual(
            text_plugin_versions.count(),
            text_plugin_versions_initial_count + 1,
        )

        # move plugin back to native
        request = self.get_post_request({
            'placeholder_id': n_pl_pk,
            'plugin_id': text_plugin_pk,
        })
        response = m_pl_admin.move_plugin(request)
        self.assertEqual(response.status_code, 200)

        # assert a new version for the manual placeholder has been created
        self.assertEqual(
            m_pl_versions.count(),
            m_pl_versions_initial_count + 2,
        )

        # assert manual placeholder revision comment was set correctly
        self.assertEqual(
            m_pl_revisions.latest('pk').comment,
            'Moved plugins to %s' % force_text(n_pl),
        )

        # assert a new version for the native placeholder has been created
        self.assertEqual(
            n_pl_versions.count(),
            n_pl_versions_initial_count + 2,
        )

        # assert native placeholder revision comment was set correctly
        self.assertEqual(
            n_pl_revisions.latest('pk').comment,
            'Moved plugins to %s' % force_text(n_pl),
        )

        # assert a new version for the text plugin has been created
        self.assertEqual(
            text_plugin_versions.count(),
            text_plugin_versions_initial_count + 2,
        )

        # move plugin to static placeholder
        request = self.get_post_request({
            'placeholder_id': static_placeholder.pk,
            'plugin_id': text_plugin_pk,
        })
        response = n_pl_admin.move_plugin(request)
        self.assertEqual(response.status_code, 200)

        # assert a new version for the native placeholder has been created
        self.assertEqual(
            n_pl_versions.count(),
            n_pl_versions_initial_count + 3,
        )

        # assert native placeholder revision comment was set correctly
        self.assertEqual(
            n_pl_revisions.latest('pk').comment,
            'Moved plugins to %s' % force_text(static_placeholder),
        )

        # move plugin back to native
        request = self.get_post_request({
            'placeholder_id': n_pl_pk,
            'plugin_id': text_plugin_pk,
        })
        response = static_placeholder_admin.move_plugin(request)
        self.assertEqual(response.status_code, 200)

        # assert a new version for the native placeholder has been created
        self.assertEqual(
            n_pl_versions.count(),
            n_pl_versions_initial_count + 4,
        )

        # assert native placeholder revision comment was set correctly
        self.assertEqual(
            n_pl_revisions.latest('pk').comment,
            'Moved plugins to %s' % force_text(n_pl),
        )

        # assert a new version for the text plugin has been created
        self.assertEqual(
            text_plugin_versions.count(),
            text_plugin_versions_initial_count + 3,
        )

    @unittest.skipUnless(CMS_3_2_1, "CMS 3.2.1+ fixed reversion support.")
    def test_revision_on_plugin_move_a_copy(self):
        from cms.plugin_pool import plugin_pool

        pl_versions = self.get_placeholder_versions()

        TextPluginModel = plugin_pool.get_plugin('TextPlugin').model
        text_plugin_c_type = ContentType.objects.get_for_model(TextPluginModel)

        # three placeholder types
        # native - native CMS placeholder (created using a placeholder tag)
        # manual - Manual placeholder (created using a PlaceholderField)
        # static - Static placeholder (created using the staticplaceholder tag)

        n_pl_page = create_page('test page', 'simple.html', u'en')
        n_pl = n_pl_page.placeholders.get(slot='content_1')
        n_pl_pk = n_pl.pk
        n_pl_admin = self.get_page_admin()
        n_pl_versions = pl_versions.filter(object_id_int=n_pl_pk)
        n_pl_revisions = Revision.objects.filter(version__in=n_pl_versions)
        n_pl_versions_initial_count = n_pl_versions.count()

        example = WithPlaceholder.objects.create()
        m_pl = example.content
        m_pl_admin = self.get_example_admin()
        m_pl_versions = pl_versions.filter(object_id_int=m_pl.pk)
        m_pl_revisions = Revision.objects.filter(version__in=m_pl_versions)
        m_pl_versions_initial_count = m_pl_versions.count()

        static_placeholder_obj = StaticPlaceholder.objects.create(
            name='static',
            code='static',
            site_id=1,
        )
        static_placeholder = static_placeholder_obj.draft
        static_placeholder_admin = self.get_staticplaceholder_admin()

        data = {
            'placeholder': n_pl,
            'plugin_type': 'TextPlugin',
            'language': 'en',
        }

        # Add plugin to native placeholder
        text_plugin = add_plugin(**data)
        text_plugin_pk = text_plugin.pk
        text_plugin_versions = Version.objects.filter(
            content_type=text_plugin_c_type,
        )

        # copy plugin from native to manual placeholder
        response = self.move_a_copy(
            admin=n_pl_admin,
            placeholder_id=m_pl.pk,
            plugin_id=text_plugin_pk,
        )

        self.assertEqual(response.status_code, 200)

        # Point to the newly created text plugin
        text_plugin_pk = self.get_plugin_id_from_response(
            response,
            path='urls.edit_plugin',
        )

        # assert native placeholder version count remains the same
        self.assertEqual(
            n_pl_versions.count(),
            # We use 2 because there's two placeholders
            # in the native placeholder page
            n_pl_versions_initial_count,
        )

        # assert a new version for the manual placeholder has been created
        self.assertEqual(
            m_pl_versions.count(),
            m_pl_versions_initial_count + 1,
        )

        # assert revision comment was set correctly
        self.assertEqual(
            m_pl_revisions.latest('pk').comment,
            'Copied plugins to %s' % force_text(m_pl),
        )

        # assert a new version for the text plugin has been created
        self.assertEqual(
            text_plugin_versions.filter(object_id_int=text_plugin_pk).count(),
            1,
        )

        # copy plugin from manual to native placeholder
        response = self.move_a_copy(
            admin=m_pl_admin,
            placeholder_id=n_pl.pk,
            plugin_id=text_plugin_pk,
        )

        self.assertEqual(response.status_code, 200)

        # Point to the newly created text plugin
        text_plugin_pk = self.get_plugin_id_from_response(
            response,
            path='urls.edit_plugin',
        )

        # assert manual placeholder version count remains the same
        self.assertEqual(
            m_pl_versions.count(),
            # We use 2 because there's two placeholders
            # in the native placeholder page
            m_pl_versions_initial_count + 1,
        )

        # assert a new version for the native placeholder has been created
        self.assertEqual(
            n_pl_versions.count(),
            n_pl_versions_initial_count + 1,
        )

        # assert native placeholder revision comment was set correctly
        self.assertEqual(
            n_pl_revisions.latest('pk').comment,
            'Copied plugins to %s' % force_text(n_pl),
        )

        # assert a new version for the text plugin has been created
        self.assertEqual(
            text_plugin_versions.filter(object_id_int=text_plugin_pk).count(),
            1,
        )

        # copy plugin from native to static placeholder
        response = self.move_a_copy(
            admin=n_pl_admin,
            placeholder_id=static_placeholder.pk,
            plugin_id=text_plugin_pk,
        )

        self.assertEqual(response.status_code, 200)

        # Point to the newly created text plugin
        text_plugin_pk = self.get_plugin_id_from_response(
            response,
            path='urls.edit_plugin',
        )

        # assert native placeholder version count remains the same
        self.assertEqual(
            n_pl_versions.count(),
            n_pl_versions_initial_count + 1,
        )

        # copy plugin from static to native placeholder
        response = self.move_a_copy(
            admin=static_placeholder_admin,
            placeholder_id=n_pl.pk,
            plugin_id=text_plugin_pk,
        )

        self.assertEqual(response.status_code, 200)

        # Point to the newly created text plugin
        text_plugin_pk = self.get_plugin_id_from_response(
            response,
            path='urls.edit_plugin',
        )

        # assert a new version for the native placeholder has been created
        self.assertEqual(
            n_pl_versions.count(),
            n_pl_versions_initial_count + 2,
        )

        # assert native placeholder revision comment was set correctly
        self.assertEqual(
            n_pl_revisions.latest('pk').comment,
            'Copied plugins to %s' % force_text(n_pl),
        )

        # assert a new version for the text plugin has been created
        self.assertEqual(
            text_plugin_versions.filter(object_id_int=text_plugin_pk).count(),
            1,
        )

    def test_revision_view_reverts_object_to_selected_state(self):
        from cms.plugin_pool import plugin_pool

        SamplePluginModel = plugin_pool.get_plugin('SamplePlugin').model
        s_plugin_c_type = ContentType.objects.get_for_model(SamplePluginModel)

        example_obj = WithPlaceholder.objects.create()

        m_pl = example_obj.content
        m_pl_admin = self.get_example_admin()

        example_obj_versions = (
            m_pl_admin
            .revision_manager
            .get_for_object(example_obj)
            .order_by("-pk")
        )

        data = {
            'plugin_type': 'SamplePlugin',
            'placeholder_id': m_pl.pk,
            'plugin_language': 'en',
        }

        if CMS_3_3:
            request = self.get_su_request(post_data={})
            request.GET = QueryDict(urlencode(data))
            request._dont_enforce_csrf_checks = True
        else:
            request = self.get_post_request(data)

        # first plugin
        response = m_pl_admin.add_plugin(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(m_pl.cmsplugin_set.count(), 1)

        # First version for example obj
        example_obj_v1 = example_obj_versions[0]

        # Point to the newly created sample plugin
        sample_plugin_pk = m_pl.cmsplugin_set.get().pk

        sample_plugin_versions = (
            example_obj_v1.revision.version_set.all()
            .filter(
                content_type=s_plugin_c_type,
                object_id_int=sample_plugin_pk
            ).count()
        )

        # assert a new version for the sample plugin has been created
        self.assertEqual(
            sample_plugin_versions,
            1,
        )

        # second plugin
        response = m_pl_admin.add_plugin(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(m_pl.cmsplugin_set.count(), 2)

        # Second version for example obj
        example_obj_v2 = example_obj_versions[0]

        # Point to the newly created sample plugin
        sample_plugin_pk = m_pl.cmsplugin_set.latest('id').pk

        sample_plugin_versions = (
            example_obj_v2.revision.version_set.all()
            .filter(
                content_type=s_plugin_c_type,
                object_id_int=sample_plugin_pk
            ).count()
        )

        # assert a new version for the text plugin has been created
        self.assertEqual(
            sample_plugin_versions,
            1,
        )

        # third plugin
        response = m_pl_admin.add_plugin(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(m_pl.cmsplugin_set.count(), 3)

        # third version for example obj
        example_obj_v3 = example_obj_versions[0]

        # Point to the newly created sample plugin
        sample_plugin_pk = m_pl.cmsplugin_set.latest('id').pk

        sample_plugin_versions = (
            example_obj_v3.revision.version_set.all()
            .filter(
                content_type=s_plugin_c_type,
                object_id_int=sample_plugin_pk
            ).count()
        )

        # assert a new version for the text plugin has been created
        self.assertEqual(
            sample_plugin_versions,
            1,
        )

        self.assertEqual(m_pl.cmsplugin_set.count(), 3)

        request = self.get_post_request(data={})

        # revert to the example object's version 1
        m_pl_admin.revision_view(
            request,
            str(example_obj.pk),
            str(example_obj_v1.pk),
        )

        self.assertEqual(response.status_code, 200)

        # assert that only one plugin is present
        self.assertEqual(m_pl.cmsplugin_set.count(), 1)

        # revert to the example object's version 3
        m_pl_admin.revision_view(
            request,
            str(example_obj.pk),
            str(example_obj_v3.pk),
        )

        self.assertEqual(response.status_code, 200)

        # assert that all three plugin is present
        self.assertEqual(m_pl.cmsplugin_set.count(), 3)

        # revert to the example object's version 2
        m_pl_admin.revision_view(
            request,
            str(example_obj.pk),
            str(example_obj_v2.pk),
        )

        self.assertEqual(response.status_code, 200)

        # assert that only two plugin is present
        self.assertEqual(m_pl.cmsplugin_set.count(), 2)
