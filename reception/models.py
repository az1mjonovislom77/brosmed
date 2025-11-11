from django.db import models

from department.models import Department
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

    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=100, choices=GenderChoice.choices)
    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    disease = models.TextField(null=True, blank=True)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    payment_status = models.CharField(max_length=100, choices=PaymentStatus.choices, default=PaymentStatus.pending)
    patient_status = models.CharField(max_length=100, choices=PatientStatus.choices, null=True, blank=True)

    def __str__(self):
        return self.name + ' ' + self.last_name
