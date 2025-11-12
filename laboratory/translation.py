from modeltranslation.translator import register, TranslationOptions

from laboratory.models import Analysis


@register(Analysis)
class AnalysisTranslation(TranslationOptions):
    fields = ('analysis_result',)
