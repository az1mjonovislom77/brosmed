from modeltranslation.translator import register, TranslationOptions

from doctor.models import Consultations


@register(Consultations)
class ConsultationsTranslation(TranslationOptions):
    fields = ('diagnosis', 'recommendation', 'recipe')
