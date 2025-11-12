from modeltranslation.translator import register, TranslationOptions

from reception.models import Patient


@register(Patient)
class PatientTranslation(TranslationOptions):
    fields = ('disease',)
