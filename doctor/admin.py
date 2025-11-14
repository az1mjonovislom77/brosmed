from django.contrib import admin

from doctor.models import Consultations


@admin.register(Consultations)
class ConsultationsAdmin(admin.ModelAdmin):
    list_display = ('id','patient', 'diagnosis', 'recipe', 'patient_status')
