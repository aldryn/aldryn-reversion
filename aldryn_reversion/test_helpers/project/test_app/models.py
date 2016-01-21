# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models

from parler.models import TranslatableModel, TranslatedFields
from cms.models.fields import PlaceholderField

from aldryn_reversion.core import version_controlled_content


@version_controlled_content
class SimpleRegistered(models.Model):
    """
    Represents the simplest possible model.
    """
    position = models.IntegerField()


@version_controlled_content
class SimpleNoAdmin(models.Model):
    """
    Represents the simplest possible model, but with no admin class, so
    that user cannot access revert view.
    """
    position = models.IntegerField()


@version_controlled_content
class WithTranslations(TranslatableModel):
    """
    Simple model with translated fields.
    """
    translations = TranslatedFields(
        description=models.CharField(max_length=255)
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


@version_controlled_content
class WithPlaceholder(models.Model):
    """
    Simple model with PlaceholderField.
    """
    content = PlaceholderField('WithPlaceholder Content ph')


@version_controlled_content(follow=['simple_relation'])
class SimpleFK(models.Model):
    """
    Simple relation to model which is not registered with reversions admin,
    and can be restored only in automatical mode.
    """
    simple_relation = models.ForeignKey(SimpleNoAdmin)


@version_controlled_content(follow=['simple_relation'])
class SimpleRequiredFK(models.Model):
    """
    Simple relation to model which is registered with reversions admin,
    and FK is required
    """
    simple_relation = models.ForeignKey(SimpleRegistered, null=True,
                                        on_delete=models.SET_NULL)


@version_controlled_content(follow=['simple_relation'])
class ComplexOneFK(TranslatableModel):
    """
    FK, placeholders, translations
    """
    translations = TranslatedFields(
        complex_description=models.TextField(max_length=500)
    )
    complex_content = PlaceholderField('ComplexOneFK complex_content ph')
    simple_relation = models.ForeignKey(WithPlaceholder)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


@version_controlled_content(follow=['simple_relation'])
class BlankFK(models.Model):
    """
    Simple model with not required FK relation.
    """
    simple_relation = models.ForeignKey(SimpleRegistered, blank=True, null=True)


@version_controlled_content(follow=['first_relation', 'second_relation'])
class MultiLevelFK(models.Model):
    """
    Few levels of foreign key relations, to test multilevel recovery.
    Level means there is a relation to an object which is also related to
    other object, i.e.:
        MultiLevelFK -> SimpleFK -> SimpleNoAdmin and
        MultiLevelFK -> ComplexOneFK -> WithPlaceholder
    """
    first_relation = models.ForeignKey(
        SimpleFK, blank=True, null=True, on_delete=models.SET_NULL)
    second_relation = models.ForeignKey(ComplexOneFK)


@version_controlled_content(follow=['self_relation'])
class FKtoSelf(models.Model):
    """
    Recursive relations model.
    """
    self_relation = models.ForeignKey(
        'self', on_delete=models.CASCADE, related_name='incoming_relations',
        blank=True)
