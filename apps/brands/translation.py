# apps/brands/translation.py
from modeltranslation.translator import register, TranslationOptions
from .models import Brand, CarModel


@register(Brand)
class BrandTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(CarModel)
class CarModelTranslationOptions(TranslationOptions):
    fields = ('name',)