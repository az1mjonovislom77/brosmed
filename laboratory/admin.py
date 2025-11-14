from django.contrib import admin

from laboratory.models import Analysis, AnalysisFile


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'analysis_result', 'status')

@admin.register(AnalysisFile)
class AnalysisFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'analysis')
