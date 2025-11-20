from rest_framework import serializers

from department.models import Department, DepartmentTypes, Result
from reception.models import AnalysisResult


class AnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = ['id', 'patient', 'analysis_result']


class AnalysisResultListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        result_id = self.context['result_id']
        objs = []
        for item in validated_data:
            objs.append(AnalysisResult(result_id=result_id, analysis_result=item['analysis_result']))
        return AnalysisResult.objects.bulk_create(objs)


class AnalysisResultCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = ['result', 'patient', 'analysis_result', 'created_at']


class AnalysisResultPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = ['id', 'result', 'patient',  'analysis_result',  'created_at']


class ResultSerializer(serializers.ModelSerializer):
    analysis_result = AnalysisResultSerializer(many=True, required=False)

    class Meta:
        model = Result
        fields = ['id', 'department_types', 'title', 'norma', 'analysis_result']


class ResultGetSerializer(serializers.ModelSerializer):
    analysis_result = AnalysisResultSerializer(many=True)

    class Meta:
        model = Result
        fields = ['id', 'title', 'norma', 'analysis_result']


class DepartmentTypesSerializer(serializers.ModelSerializer):
    result = ResultGetSerializer(many=True)

    class Meta:
        model = DepartmentTypes
        fields = ['id', 'department', 'title', 'title_uz', 'title_ru', 'price', 'result']

    def create(self, validated_data):
        result_data = validated_data.pop('result', [])

        department_type = DepartmentTypes.objects.create(**validated_data)

        for res in result_data:
            analysis_result_data = res.pop('analysis_result', [])

            result_obj = Result.objects.create(department_types=department_type, **res)

            for ar in analysis_result_data: AnalysisResult.objects.create(result=result_obj, **ar)

        return department_type


class DepartmentSerializer(serializers.ModelSerializer):
    department_types = DepartmentTypesSerializer(read_only=True, many=True)

    class Meta:
        model = Department
        fields = ['id', 'title', 'title_uz', 'title_ru', 'department_types']
