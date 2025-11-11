from django.contrib import admin

from reception.models import Patient
from user.models import User


class PatientInline(admin.TabularInline):
    model = Patient
    extra = 1


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'full_name', 'role')
    inlines = [PatientInline]
