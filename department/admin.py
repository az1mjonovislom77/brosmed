from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from department.models import Department, DepartmentTypes
from reception.models import Patient


class PatientInline(admin.TabularInline):
    model = Patient
    extra = 1


@admin.register(Department)
class DepartmentAdmin(TranslationAdmin):
    list_display = ('id', 'title')
    inlines = [PatientInline]


@admin.register(DepartmentTypes)
class DepartmentTypesAdmin(TranslationAdmin):
    list_display = ('id', 'title')
    inlines = [PatientInline]
