from rest_framework import serializers
from department.models import Result
from department.serializers import DepartmentTypesSerializer, DepartmentTypesNestSerializer, ResultSerializer
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
        fields = ['id', 'user', 'name', 'last_name', 'middle_name', 'passport', 'self_disease', 'gender',
                  'birth_date', 'payment_status', 'patient_status']


class BaseAnalysisSerializer(serializers.ModelSerializer):
    files = AnalysisFileSerializer(many=True, required=False, source='analysisfile_set')

    def create(self, validated_data):
        request = self.context.get('request')
        files = request.FILES.getlist('files')
        validated_data.pop('analysisfile_set', None)
        analysis = Analysis.objects.create(**validated_data)
        for file in files:
            AnalysisFile.objects.create(analysis=analysis, file=file)
        return analysis


class AnalysisSerializer(BaseAnalysisSerializer):
    department_types = DepartmentTypesSerializer(read_only=True)
    patient = PatientNestSerializer(read_only=True)

    class Meta:
        model = Analysis
        fields = ['id', 'patient', 'department_types', 'status', 'files']


class AnalysisPostSerializer(BaseAnalysisSerializer):
    class Meta:
        model = Analysis
        fields = ['id', 'patient', 'department_types', 'status', 'files']


class AnalysisNestSerializer(BaseAnalysisSerializer):
    department_types = DepartmentTypesNestSerializer(read_only=True)

    class Meta:
        model = Analysis
        fields = ['id', 'department_types', 'status', 'files', 'created_at']


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
        fields = ['id', 'patient', 'department_types', 'status', 'files', 'results', 'created_at']

    def get_results(self, obj):
        results = Result.objects.filter(department_types=obj.department_types)
        serialized_results = []
        for result in results:
            analysis_results = result.analysis_result.filter(patient=obj.patient)
            result_serializer = ResultSerializer(result, context=self.context)
            data = result_serializer.data
            data['analysis_result'] = AnalysisResultNestedSerializer(analysis_results, many=True,
                                                                     context=self.context).data
            serialized_results.append(data)

        return serialized_results


class AnalysisDetailInputSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(required=True)
    analysis_id = serializers.IntegerField(required=True)


class AnalysisByPatientInputSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(required=True)
