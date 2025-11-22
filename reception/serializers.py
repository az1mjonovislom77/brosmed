from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from department.serializers import DepartmentTypesNestSerializer
from reception.models import Patient, AnalysisResult, Disease
from user.serializers import UserCreateSerializer


class DiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disease
        fields = '__all__'


class PatientSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer(read_only=True)
    department_types = DepartmentTypesNestSerializer(read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user', 'department', 'department_types', 'name', 'last_name', 'middle_name', 'gender',
                  'birth_date', 'phone_number', 'passport', 'address', 'payment_status', 'patient_status',
                  'created_at']

    def get_disease(self, obj):
        return Disease.objects.filter(patient=obj).values_list("id", flat=True)


class PatientPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'user', 'department', 'department_types', 'name', 'last_name', 'middle_name', 'gender',
                  'birth_date', 'phone_number', 'passport', 'address', 'payment_status', 'patient_status',
                  'created_at']


class DiseaseGetSerializers(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)

    class Meta:
        model = Disease
        fields = ['id', 'patient', 'department', 'department_types', 'user', 'disease']


class ExportAnalysisSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(required=True, help_text="Patient ID")
    analysis_id = serializers.IntegerField(required=True, help_text="Analysis ID")


class PatientSearchInputSerializer(serializers.Serializer):
    search = serializers.CharField(required=True, help_text="Search")
