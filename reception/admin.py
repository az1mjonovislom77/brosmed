from django.contrib import admin

from doctor.models import Consultations
from reception.models import Patient, AnalysisResult, Analysis


class ConsultationsInline(admin.TabularInline):
    model = Consultations
    extra = 1

class AnalysisResultInline(admin.TabularInline):
    model = AnalysisResult
    extra = 1


class AnalysisInline(admin.TabularInline):
    model = Analysis
    extra = 1


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user')
    inlines = [AnalysisInline, ConsultationsInline, AnalysisResultInline]
