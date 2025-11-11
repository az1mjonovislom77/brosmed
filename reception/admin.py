from django.contrib import admin

from reception.models import Patient


@admin.register(Patient)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user')
