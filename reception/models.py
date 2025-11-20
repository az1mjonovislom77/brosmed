from django.db import models

from department.models import Department, DepartmentTypes, Result
from user.models import User


class Patient(models.Model):
    class GenderChoice(models.TextChoices):
        MALE = 'e', 'ERKAK'
        FEMALE = 'a', 'AYOL'

    class PaymentStatus(models.TextChoices):
        pending = 'p', 'PENDING'
        confirmed = 'c', 'CONFIRMED'
        partially_confirmed = 'pc', 'PARTIALLY CONFIRMED'

    class PatientStatus(models.TextChoices):
        in_register = 'r', 'IN REGISTER'
        in_laboratory = 'l', 'IN LABORATORY'
        in_doctor = 'd', 'IN DOCTOR'
        treating = 't', 'TREATING'
        finished = 'f', 'FINISHED'
        recovered = 'rc', 'RECOVERED'

    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    department_types = models.ForeignKey(DepartmentTypes, null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='patient_users')
    name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=100, choices=GenderChoice.choices, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    disease = models.TextField(null=True, blank=True)
    payment_status = models.CharField(max_length=100, choices=PaymentStatus.choices, default=PaymentStatus.pending)
    patient_status = models.CharField(max_length=100, choices=PatientStatus.choices, default=PatientStatus.in_register)
    partial_payment_amount = models.FloatField(default=0)
    total_amount = models.FloatField(default=0)
    paid_amount = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.user and getattr(self.user, 'price', None):
                self.total_amount = float(self.user.price)
            elif self.department_types and getattr(self.department_types, 'price', None):
                self.total_amount = float(self.department_types.price)
            else:
                self.total_amount = 0
            self.payment_status = self.PaymentStatus.pending
            self.paid_amount = 0
            self.partial_payment_amount = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name + ' ' + self.last_name


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


class AnalysisResult(models.Model):
    result = models.ForeignKey(Result, null=True, blank=True, on_delete=models.SET_NULL, related_name='analysis_result')
    patient = models.ForeignKey(Patient, null=True, blank=True, on_delete=models.SET_NULL)
    analysis_result = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.analysis_result
