# apps/core/translation.py
from modeltranslation.translator import register, TranslationOptions
from .models import Settings, Banner


@register(Settings)
class SettingsTranslationOptions(TranslationOptions):
    fields = ('site_name',)


@register(Banner)
class BannerTranslationOptions(TranslationOptions):
    fields = ('title', 'description')