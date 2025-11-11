from django.db import models

from department.models import DepartmentTypes
from reception.models import Patient


class Analysis(models.Model):
    class Status(models.TextChoices):
        new = 'n', 'NEW'
        in_progress = 'ip', 'IN_PROGRESS'
        finished = 'f', 'FINISHED'

    patient = models.ForeignKey(Patient, null=True, blank=True, on_delete=models.SET_NULL)
    department_types = models.ForeignKey(DepartmentTypes, null=True, blank=True, on_delete=models.SET_NULL)
    analysis_result = models.CharField(max_length=100)
    status = models.CharField(max_length=100, choices=Status.choices, default=Status.new)

    def __str__(self):
        return str(self.id)


class AnalysisFile(models.Model):
    analysis = models.ForeignKey(Analysis, null=True, blank=True, on_delete=models.SET_NULL)
    file = models.FileField(upload_to='analysis/', null=True, blank=True)

    def __str__(self):
        return str(self.id)
