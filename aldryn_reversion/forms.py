from django.core.exceptions import ValidationError
from django.forms import forms
from django.forms.fields import MultipleChoiceField
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _

from .utils import (
    get_translations_versions_for_object, get_conflict_fks_versions,
)


class RecoverObjectWithTranslationForm(forms.Form):
    translations = MultipleChoiceField(
        required=True,
        widget=CheckboxSelectMultiple(),
        label=_('Translations to restore:'),
        help_text=_('Please select translations which would be restored.'))

    def __init__(self, *args, **kwargs):
        # prepare data for misc lookups
        self.revision = kwargs.pop('revision')
        self.obj = kwargs.pop('obj')
        self.version = kwargs.pop('version')
        self.resolve_conflicts = kwargs.pop('resolve_conflicts')
        self.placeholders = kwargs.pop('placeholders')
        # do not check object which needs to be recovered
        versions = self.revision.version_set.exclude(pk=self.version.pk)

        super(RecoverObjectWithTranslationForm, self).__init__(*args, **kwargs)

        translatable = hasattr(self.obj, 'translations')
        if translatable:
            translation_versions = get_translations_versions_for_object(
                self.obj, self.revision, versions)
            # update form
            choices = [(translation_version.pk, force_text(translation_version))
                       for translation_version in translation_versions]
            self.fields['translations'].choices = choices
        else:
            # do not show translations options if object is not translated
            self.fields.pop('translations')

    def clean(self):
        data = super(RecoverObjectWithTranslationForm, self).clean()
        # if there is self.resolve_conflicts do not count them as conflicts
        exclude = {
            'pk__in': [version.pk for version in
                       self.resolve_conflicts + self.placeholders]}
        conflict_fks_versions = get_conflict_fks_versions(
            self.obj, self.version, self.revision,
            exclude=exclude)
        if bool(conflict_fks_versions):
            raise ValidationError(
                _('Cannot restore object, there are conflicts!'),
                code='invalid')
        return data

    def save(self):
        # restore placeholders
        for placeholder_version in self.placeholders:
            # note that only placeholders are being reverted, assuming that
            # cms plugins that are related to this placeholder were not deleted
            placeholder_version.revert()

        # if there is self.resolve_conflicts revert those objects to avoid
        # integrity errors, because user cannot do that form admin
        # assume that that was prepared for us in admin view
        for conflict in self.resolve_conflicts:
            conflict.revert()

        # revert main object
        self.version.revert()

        # revert translations, if there is translations
        translations_pks = self.cleaned_data.get(
            'translations', []) if hasattr(self, 'cleaned_data') else []
        translation_versions = self.revision.version_set.filter(
            pk__in=translations_pks) if translations_pks else []
        for translation_version in translation_versions:
            translation_version.revert()
