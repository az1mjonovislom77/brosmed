from django.db import models
from user.models import User
from reception.models import Patient


class Consultations(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    diagnosis = models.TextField(max_length=500)
    recommendation = models.TextField(max_length=500)
    recipe = models.TextField(max_length=500)
    patient_status = models.CharField(max_length=100, choices=Patient.PatientStatus.choices, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.patient.name
