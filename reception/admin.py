from django.contrib import admin

from laboratory.models import Analysis
from reception.models import Patient


class AnalysisInline(admin.TabularInline):
    model = Analysis
    extra = 1


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user')
    inlines = [AnalysisInline]
