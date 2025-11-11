from rest_framework import serializers

from department.models import Department, DepartmentTypes


class DepartmentTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentTypes
        fields = ['id', 'department', 'title', 'title_uz', 'title_ru']


class DepartmentSerializer(serializers.ModelSerializer):
    department_types = DepartmentTypesSerializer(read_only=True, many=True)

    class Meta:
        model = Department
        fields = ['id', 'title', 'title_uz', 'title_ru', 'department_types']
