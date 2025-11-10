from rest_framework import serializers

from department.models import Department, DepartmentTypes


class DepartmentTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentTypes
        fields = ['id', 'title', 'title_uz', 'title_ru']


class DepartmentSerializer(serializers.ModelSerializer):
    department_types = DepartmentTypesSerializer(read_only=True, many=True)
    department_types_id = serializers.PrimaryKeyRelatedField(queryset=DepartmentTypes.objects.all(),
                                                             source='department_types', many=True, write_only=True)

    class Meta:
        model = Department
        fields = ['id', 'title', 'title_uz', 'title_ru', 'department_types', 'department_types_id']
