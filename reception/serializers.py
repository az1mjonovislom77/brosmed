from rest_framework import serializers

from doctor.serializers import ConsultationsSerializer
from reception.models import Patient


class PatientSerializer(serializers.ModelSerializer):
    consultations = ConsultationsSerializer(many=True, read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user', 'department', 'department_types', 'name', 'last_name', 'middle_name', 'gender',
                  'birth_date', 'phone_number', 'address', 'disease', 'disease_uz', 'disease_ru', 'payment_status',
                  'patient_status', 'created_at', 'consultations']
