from rest_framework import serializers

from department.serializers import DepartmentTypesSerializer, DepartmentTypesNestSerializer
from reception.models import Patient, AnalysisFile, Analysis, AnalysisResult


class AnalysisFileSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisFile
        fields = ['id', 'file']

    def get_file(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url)
        return None


class PatientNestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'user', 'name', 'last_name', 'middle_name', 'gender',
                  'birth_date', 'payment_status',
                  'patient_status', 'created_at']


class AnalysisSerializer(serializers.ModelSerializer):
    files = AnalysisFileSerializer(many=True, required=False, source='analysisfile_set')
    department_types = DepartmentTypesSerializer(read_only=True)
    patient = PatientNestSerializer(read_only=True)

    class Meta:
        model = Analysis
        fields = ['id', 'patient', 'department_types', 'status', 'files']

    def create(self, validated_data):
        request = self.context.get('request')

        files = request.FILES.getlist('files')
        validated_data.pop('analysisfile_set', None)
        analysis = Analysis.objects.create(**validated_data)
        for file in files:
            AnalysisFile.objects.create(analysis=analysis, file=file)

        return analysis


class AnalysisPostSerializer(serializers.ModelSerializer):
    files = AnalysisFileSerializer(many=True, required=False, source='analysisfile_set')

    class Meta:
        model = Analysis
        fields = ['id', 'patient', 'department_types', 'status', 'files']

    def create(self, validated_data):
        request = self.context.get('request')
        files = request.FILES.getlist('files')

        validated_data.pop('analysisfile_set', None)

        analysis = Analysis.objects.create(**validated_data)

        for file in files:
            AnalysisFile.objects.create(analysis=analysis, file=file)

        return analysis


class AnalysisNestSerializer(serializers.ModelSerializer):
    files = AnalysisFileSerializer(many=True, required=False, source='analysisfile_set')
    department_types = DepartmentTypesNestSerializer(read_only=True)

    class Meta:
        model = Analysis
        fields = ['id', 'department_types', 'status', 'files']

    def create(self, validated_data):
        request = self.context.get('request')

        files = request.FILES.getlist('files')
        validated_data.pop('analysisfile_set', None)
        analysis = Analysis.objects.create(**validated_data)
        for file in files:
            AnalysisFile.objects.create(analysis=analysis, file=file)

        return analysis


class AnalysisSearchInputSerializer(serializers.Serializer):
    search = serializers.CharField(required=True)


class AnalysisResultNestedSerializer(serializers.ModelSerializer):
    result_name = serializers.CharField(source='result.name', read_only=True)

    class Meta:
        model = AnalysisResult
        fields = ['id', 'result_name', 'analysis_result']


class AnalysisFullDetailSerializer(serializers.ModelSerializer):
    files = AnalysisFileSerializer(many=True, source='analysisfile_set')
    patient = PatientNestSerializer(read_only=True)
    department_types = DepartmentTypesNestSerializer(read_only=True)
    results = serializers.SerializerMethodField()

    class Meta:
        model = Analysis
        fields = [
            'id',
            'patient',
            'department_types',
            'status',
            'files',
            'results'
        ]

    def get_results(self, obj):
        results = AnalysisResult.objects.filter(patient=obj.patient)
        return AnalysisResultNestedSerializer(results, many=True).data

class AnalysisDetailInputSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(required=True)
    analysis_id = serializers.IntegerField(required=True)