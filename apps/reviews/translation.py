# apps/reviews/translation.py
from modeltranslation.translator import register, TranslationOptions
from .models import Review


@register(Review)
class ReviewTranslationOptions(TranslationOptions):
    fields = ('comment',)