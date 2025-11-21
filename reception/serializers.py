from rest_framework import serializers

from department.serializers import DepartmentTypesNestSerializer
from doctor.serializers import ConsultationsSerializer
from laboratory.serializers import AnalysisNestSerializer
from reception.models import Patient, AnalysisResult
from user.serializers import UserCreateSerializer


class PatientSerializer(serializers.ModelSerializer):
    consultations = ConsultationsSerializer(many=True, read_only=True)
    analysis = AnalysisNestSerializer(read_only=True, many=True)
    user = UserCreateSerializer(read_only=True)
    department_types = DepartmentTypesNestSerializer(read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user', 'department', 'department_types', 'name', 'last_name', 'middle_name', 'gender',
                  'birth_date', 'phone_number', 'address', 'disease', 'disease_uz', 'disease_ru', 'payment_status',
                  'patient_status', 'created_at', 'consultations', 'analysis']

    def get_results(self, obj):
        return AnalysisResult.objects.filter(patient=obj).values_list("id", flat=True)


class PatientPostSerializer(serializers.ModelSerializer):
    consultations = ConsultationsSerializer(many=True, read_only=True)
    analysis = AnalysisNestSerializer(read_only=True, many=True, source='patient')

    class Meta:
        model = Patient
        fields = ['id', 'user', 'department', 'department_types', 'name', 'last_name', 'middle_name', 'gender',
                  'birth_date', 'phone_number', 'address', 'disease', 'disease_uz', 'disease_ru', 'payment_status',
                  'patient_status', 'created_at', 'consultations', 'analysis']
