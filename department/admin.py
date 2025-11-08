from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from department.models import Department, DepartmentTypes


@admin.register(Department)
class DepartmentAdmin(TranslationAdmin):
    list_display = ('id', 'title')


@admin.register(DepartmentTypes)
class DepartmentTypesAdmin(TranslationAdmin):
    list_display = ('id', 'title')
