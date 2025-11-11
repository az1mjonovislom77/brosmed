from rest_framework import serializers

from reception.models import Patient


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'user', 'department', 'name', 'last_name', 'middle_name', 'gender', 'birth_date', 'phone_number',
                  'address', 'disease','payment_status', 'patient_status']
