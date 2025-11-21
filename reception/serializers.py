from rest_framework import serializers

from department.serializers import DepartmentTypesNestSerializer
from reception.models import Patient, AnalysisResult
from user.serializers import UserCreateSerializer


class PatientSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer(read_only=True)
    department_types = DepartmentTypesNestSerializer(read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user', 'department', 'department_types', 'name', 'last_name', 'middle_name', 'gender',
                  'birth_date', 'phone_number', 'address', 'disease', 'disease_uz', 'disease_ru', 'payment_status',
                  'patient_status', 'created_at']

    def get_results(self, obj):
        return AnalysisResult.objects.filter(patient=obj).values_list("id", flat=True)


class PatientPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'user', 'department', 'department_types', 'name', 'last_name', 'middle_name', 'gender',
                  'birth_date', 'phone_number', 'address', 'disease', 'disease_uz', 'disease_ru', 'payment_status',
                  'patient_status', 'created_at']
