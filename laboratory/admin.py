from django.contrib import admin

from laboratory.models import Analysis, AnalysisFile, Result


class ResultInline(admin.TabularInline):
    model = Result
    extra = 1


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'status')
    inlines = [ResultInline]


@admin.register(AnalysisFile)
class AnalysisFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'analysis')


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'analysis', 'title', 'norma',)
