from rest_framework import serializers

from department.models import Department, DepartmentTypes, Result


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ['id', 'department_types', 'title', 'analysis_result', 'norma']


class ResultGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ['id', 'title', 'analysis_result', 'norma']


class DepartmentTypesSerializer(serializers.ModelSerializer):
    result = ResultGetSerializer(many=True)

    class Meta:
        model = DepartmentTypes
        fields = ['id', 'department', 'title', 'title_uz', 'title_ru', 'price', 'result']

    def create(self, validated_data):
        result_data = validated_data.pop('result', [])

        department_type = DepartmentTypes.objects.create(**validated_data)

        for r in result_data:
            Result.objects.create(department_types=department_type, **r)

        return department_type


class DepartmentSerializer(serializers.ModelSerializer):
    department_types = DepartmentTypesSerializer(read_only=True, many=True)

    class Meta:
        model = Department
        fields = ['id', 'title', 'title_uz', 'title_ru', 'department_types']
