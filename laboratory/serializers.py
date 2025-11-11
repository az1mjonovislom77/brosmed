from rest_framework import serializers

from laboratory.models import Analysis, AnalysisFile


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


class AnalysisSerializer(serializers.ModelSerializer):
    files = AnalysisFileSerializer(many=True, required=False, source='analysisfile_set')

    class Meta:
        model = Analysis
        fields = ['id', 'patient', 'department_types', 'analysis_result', 'status', 'files']

    def create(self, validated_data):
        request = self.context.get('request')

        files = request.FILES.getlist('files')
        validated_data.pop('analysisfile_set', None)
        analysis = Analysis.objects.create(**validated_data)
        for file in files:
            AnalysisFile.objects.create(analysis=analysis, file=file)

        return analysis
