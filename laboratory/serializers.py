from rest_framework import serializers

from department.serializers import DepartmentTypesSerializer
from laboratory.models import Analysis, AnalysisFile, Result
from reception.models import Patient


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ['id', 'analysis', 'title', 'analysis_result', 'norma']


class ResultNestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ['id', 'title', 'analysis_result', 'norma']



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
    result = ResultNestSerializer(many=True, read_only=True)

    class Meta:
        model = Analysis
        fields = ['id', 'patient', 'department_types', 'status', 'files', 'result']

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
    result = ResultNestSerializer(many=True)

    class Meta:
        model = Analysis
        fields = ['id', 'patient', 'department_types', 'status', 'files', 'result']

    def create(self, validated_data):
        request = self.context.get('request')
        files = request.FILES.getlist('files')

        results_data = validated_data.pop('result', [])
        validated_data.pop('analysisfile_set', None)

        analysis = Analysis.objects.create(**validated_data)

        for file in files:
            AnalysisFile.objects.create(analysis=analysis, file=file)

        for result_data in results_data:
            Result.objects.create(analysis=analysis, **result_data)

        return analysis


class AnalysisNestSerializer(serializers.ModelSerializer):
    files = AnalysisFileSerializer(many=True, required=False, source='analysisfile_set')
    department_types = DepartmentTypesSerializer(read_only=True)
    result = ResultNestSerializer(many=True)

    class Meta:
        model = Analysis
        fields = ['id', 'department_types', 'status', 'files', 'result']

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
