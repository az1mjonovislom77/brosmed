from rest_framework import serializers

from department.models import Department, DepartmentTypes, Result, AnalysisResult


class AnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = ['id', 'analysis_result']


class ResultSerializer(serializers.ModelSerializer):
    analysis_result = AnalysisResultSerializer()

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
