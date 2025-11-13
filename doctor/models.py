from django.db import models

from reception.models import Patient


class Consultations(models.Model):
    class PatientStatus(models.TextChoices):
        in_register = 'r', 'IN REGISTER'
        in_laboratory = 'l', 'IN LABORATORY'
        in_doctor = 'd', 'IN DOCTOR'
        treating = 't', 'TREATING'
        finished = 'f', 'FINISHED'
        recovered = 'rc', 'RECOVERED'

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    diagnosis = models.TextField(max_length=500)
    recommendation = models.TextField(max_length=500)
    recipe = models.TextField(max_length=500)
    patient_status = models.CharField(max_length=100, choices=PatientStatus.choices, null=True, blank=True)

    def __str__(self):
        return self.patient.name
