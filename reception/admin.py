from django.contrib import admin

from doctor.models import Consultations
from laboratory.models import Analysis
from reception.models import Patient


class ConsultationsInline(admin.TabularInline):
    model = Consultations
    extra = 1


class AnalysisInline(admin.TabularInline):
    model = Analysis
    extra = 1


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user')
    inlines = [AnalysisInline, ConsultationsInline]
