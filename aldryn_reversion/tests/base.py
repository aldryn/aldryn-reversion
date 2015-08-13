# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import six
import reversion

from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils.translation import override
from django.test import TransactionTestCase


def get_latest_version_for_object(obj):
        version = reversion.get_for_object(obj)[0]
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
                                      is_superuser=True)
        return super_user

    def create_with_revision(self, kls, language='en', **kwargs):
        """
        Create an instance of class kls with passing kwargs to
        kls.objects.create(**kwargs)
        """
        with transaction.atomic():
            with reversion.create_revision():
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
            with reversion.create_revision():
                obj.save()

    def create_revision(self, obj, content=None, **kwargs):
        with transaction.atomic():
            with reversion.create_revision():
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
            reversion.get_for_object(
                object_with_revision)))[revision_number - 1]
        version.revision.revert()
