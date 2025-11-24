from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from department.models import Department, DepartmentTypes, Result
from reception.models import Patient, AnalysisResult


class ResultInline(admin.TabularInline):
    model = Result
    extra = 1


class AnalysisResultInline(admin.TabularInline):
    model = AnalysisResult
    extra = 1


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
    inlines = [PatientInline, ResultInline]


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'department_types', 'title', 'norma',)
    inlines = [AnalysisResultInline]
