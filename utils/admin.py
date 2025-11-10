from django.contrib import admin

from utils.models import ClinicAbout


@admin.register(ClinicAbout)
class ClinicAboutAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
