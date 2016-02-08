# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import admin

from parler.admin import TranslatableAdmin
from aldryn_reversion.admin import VersionedPlaceholderAdminMixin
from cms.admin.placeholderadmin import FrontendEditableAdminMixin

from .models import (
    SimpleRegistered, WithTranslations, WithPlaceholder, SimpleFK,
    ComplexOneFK, BlankFK, MultiLevelFK, FKtoSelf, SimpleRequiredFK
)


class SimpleRegisteredAdmin(VersionedPlaceholderAdminMixin, admin.ModelAdmin):
    list_display = ('pk', 'position')


class WithTranslationsAdmin(VersionedPlaceholderAdminMixin,
                            TranslatableAdmin):
    pass


class WithPlaceholdersAdmin(VersionedPlaceholderAdminMixin,
                            FrontendEditableAdminMixin,
                            admin.ModelAdmin):
    pass


class SimpleFKAdmin(VersionedPlaceholderAdminMixin, admin.ModelAdmin):
    pass


class SimpleRequiredFKAdmin(VersionedPlaceholderAdminMixin, admin.ModelAdmin):
    pass


class ComplexOneFKAdmin(VersionedPlaceholderAdminMixin,
                        FrontendEditableAdminMixin,
                        TranslatableAdmin):
    pass


class BlankFKAdmin(VersionedPlaceholderAdminMixin, admin.ModelAdmin):
    pass


class MultiLevelFKAdmin(VersionedPlaceholderAdminMixin, admin.ModelAdmin):
    pass


class FKtoSelfAdmin(VersionedPlaceholderAdminMixin, admin.ModelAdmin):
    pass


admin.site.register(SimpleRegistered, SimpleRegisteredAdmin)
admin.site.register(WithTranslations, WithTranslationsAdmin)
admin.site.register(WithPlaceholder, WithPlaceholdersAdmin)
admin.site.register(SimpleFK, SimpleFKAdmin)
admin.site.register(SimpleRequiredFK, SimpleRequiredFKAdmin)
admin.site.register(ComplexOneFK, ComplexOneFKAdmin)
admin.site.register(BlankFK, BlankFKAdmin)
admin.site.register(MultiLevelFK, MultiLevelFKAdmin)
admin.site.register(FKtoSelf, FKtoSelfAdmin)
