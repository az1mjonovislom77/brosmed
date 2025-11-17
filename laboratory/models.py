from django.db import models

from department.models import DepartmentTypes
from reception.models import Patient


class Analysis(models.Model):
    class Status(models.TextChoices):
        new = 'n', 'NEW'
        in_progress = 'ip', 'IN_PROGRESS'
        finished = 'f', 'FINISHED'

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='patient')
    department_types = models.ForeignKey(DepartmentTypes, null=True, blank=True, on_delete=models.SET_NULL,
                                         related_name='department_types')
    status = models.CharField(max_length=100, choices=Status.choices, default=Status.new)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class AnalysisFile(models.Model):
    analysis = models.ForeignKey(Analysis, null=True, blank=True, on_delete=models.SET_NULL)
    file = models.FileField(upload_to='analysis/', null=True, blank=True)

    def __str__(self):
        return str(self.id)


class Result(models.Model):
    analysis = models.ForeignKey(Analysis, null=True, blank=True, on_delete=models.SET_NULL, related_name='result')
    title = models.CharField(null=True, blank=True, max_length=500)
    analysis_result = models.CharField(max_length=100, null=True, blank=True)
    norma = models.CharField(null=True, blank=True, max_length=500)

    def __str__(self):
        return self.title
