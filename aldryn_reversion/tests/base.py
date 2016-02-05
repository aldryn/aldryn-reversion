# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import six

from reversion.models import Version
from reversion.revisions import (
    revision_context_manager, default_revision_manager)

from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.auth.hashers import make_password
from django.contrib.messages.storage.fallback import FallbackStorage
from django.utils.translation import override
from django.test import RequestFactory, TransactionTestCase

from cms.utils.i18n import get_language_list

from aldryn_reversion.test_helpers.project.test_app.models import (
    SimpleNoAdmin, SimpleRegistered, WithTranslations, WithPlaceholder,
    SimpleFK, BlankFK, ComplexOneFK, MultiLevelFK, SimpleRequiredFK,
)


def get_version_for_object(obj, revision_pk=None):
    """
    Return version for object, if revision_pk is provided - returns a version
    from that specific revision. No exception handling! if you get exceptions
    check your logic.
    :param obj: revisionable object
    :param revision_pk: int revision pk
    :return: reversion.models.Version
    """
    versions = default_revision_manager.get_for_object(obj)
    if revision_pk is not None:
        versions = versions.filter(revision__pk=revision_pk)
    version = versions[0]
    return version


class ReversionBaseTestCase(TransactionTestCase):

    raw_text_string = {
        'en': 'just {0} raw string',
        'de': 'just DE {0} raw string',
    }

    def setUp(self):
        super(ReversionBaseTestCase, self).setUp()

        self.staff_user_password = 'staff_pw'
        self.staff_user = self.create_staff_user(
            'staff', self.staff_user_password)
        self.super_user_password = 'super_pw'
        self.super_user = self.create_super_user(
            'super', self.super_user_password)

    def create_user(self, user_name, user_password, is_staff=False,
                    is_superuser=False):
        return User.objects.create(
            username=user_name,
            first_name='{0} first_name'.format(user_name),
            last_name='{0} last_name'.format(user_name),
            password=make_password(user_password),
            is_staff=is_staff,
            is_superuser=is_superuser
        )

    def create_staff_user(self, user_name, user_password):
        staff_user = self.create_user(user_name, user_password, is_staff=True)
        return staff_user

    def create_super_user(self, user_name, user_password):
        super_user = self.create_user(user_name, user_password,
                                      is_superuser=True, is_staff=True)
        return super_user

    def create_with_revision(self, kls, language='en', **kwargs):
        """
        Create an instance of class kls with passing kwargs to
        kls.objects.create(**kwargs)
        """
        with transaction.atomic():
            with revision_context_manager.create_revision():
                with override(language):
                    return kls.objects.create(**kwargs)

    def create_translation_with_revision(self, language, obj, **kwargs):
        """
        Just creates a translation under revision manager. Returns nothing.
        """
        # create translation outside of revision manager, and save the object
        # after that, so that revision would contain full set of related
        # objects, instead of containing only translation and no master object.
        obj.create_translation(language, **kwargs)
        with transaction.atomic():
            with revision_context_manager.create_revision():
                obj.save()

    def create_revision(self, obj, content=None, **kwargs):
        with transaction.atomic():
            with revision_context_manager.create_revision():
                # populate event with new values
                for property, value in six.iteritems(kwargs):
                    setattr(obj, property, value)
                if content:
                    # get correct plugin for language. do not update the same
                    # one.
                    language = obj.get_current_language()
                    plugins = obj.content.get_plugins().filter(
                        language=language)
                    plugin = plugins[0].get_plugin_instance()[0]
                    plugin.body = content
                    plugin.save()
                obj.save()

    def revert_to(self, object_with_revision, revision_number):
        """
        Revert <object with revision> to revision number.
        """
        # get by position, since reversion_id is not reliable,
        version = list(reversed(
            default_revision_manager.get_for_object(
                object_with_revision)))[revision_number - 1]
        version.revision.revert()

    def get_object(self, object_or_version):
        """
        Returns object regardless of type fo object_or_version.
        """
        return (object_or_version
                if type(object_or_version) != Version
                else object_or_version.object_version.object)

    def get_version(self, object_or_version):
        """
        Returns version or latest version for object, if object_or_version is
        object not reversion.models.Version.
        """
        return (object_or_version if type(object_or_version) == Version
                else get_version_for_object(object_or_version))


class HelperModelsObjectsSetupMixin(object):

    def setUp(self):
        super(HelperModelsObjectsSetupMixin, self).setUp()
        # prepare objects that can be used with utility methods
        # simple model
        self.simple_registered = self.create_with_revision(
            SimpleRegistered, position=1)

        self.simple_no_admin = self.create_with_revision(
            SimpleNoAdmin, position=42)

        # translations
        # note that WithTranslations will have 2 revisions, initial one
        # and with 'de' translation
        en_description = self.raw_text_string['en'].format(0)
        de_description = self.raw_text_string['de'].format(0)
        self.with_translation = self.create_with_revision(
            WithTranslations, description=en_description)
        self.create_translation_with_revision(
            'de', self.with_translation, description=de_description)

        # placeholders
        self.with_placeholder = self.create_with_revision(
            WithPlaceholder)

        # FK
        self.simple_fk = self.create_with_revision(
            SimpleFK, simple_relation=self.simple_no_admin)
        # blank FK means that fk is not required.
        self.blank_fk = self.create_with_revision(
            BlankFK,
            simple_relation=self.simple_registered)
        self.simple_required_fk = self.create_with_revision(
            SimpleRequiredFK, simple_relation=self.simple_registered)
        # ComplexOneFK
        self.complex_one_fk = self.create_with_revision(
            ComplexOneFK,
            simple_relation=self.with_placeholder,
            complex_description=en_description)
        self.create_translation_with_revision(
            'de', self.complex_one_fk, complex_description=de_description)
        # MultiLevelFK
        self.multi_level_fk = self.create_with_revision(
            MultiLevelFK,
            first_relation=self.simple_fk,
            second_relation=self.complex_one_fk)


class CMSRequestBasedMixin(object):
    languages = get_language_list()

    @classmethod
    def setUpClass(cls):
        super(CMSRequestBasedMixin, cls).setUpClass()
        cls.request_factory = RequestFactory()
        cls.site1 = Site.objects.get(pk=1)

    @staticmethod
    def get_request(language=None, url="/", post_data=None):
        """
        Returns a Request instance populated with cms specific attributes.
        User is not set.
        """
        request_factory = RequestFactory(HTTP_HOST=settings.ALLOWED_HOSTS[0])

        if post_data is None:
            request = request_factory.get(url)
        else:
            request = request_factory.post(url, post_data)

        request.LANGUAGE_CODE = language or settings.LANGUAGE_CODE
        # Needed for plugin rendering.
        request.current_page = None
        # session and messages
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request

    def get_su_request(self, *args, **kwargs):
        request = self.get_request(*args, **kwargs)
        request.user = self.super_user
        return request
