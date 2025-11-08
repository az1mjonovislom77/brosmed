from modeltranslation.translator import register, TranslationOptions

from department.models import Department, DepartmentTypes


@register(Department)
class DepartmentTranslation(TranslationOptions):
    fields = ('title',)


@register(DepartmentTypes)
class DepartmentTypesTranslation(TranslationOptions):
    fields = ('title',)
