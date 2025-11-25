from rest_framework import serializers
from user.models import User
from reception.models import Patient
from user.services.user_service import UserService


class PatientMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            'id', 'name', 'last_name', 'middle_name', 'gender', 'birth_date',
            'phone_number', 'passport', 'address', 'payment_status', 'patient_status'
        ]
        read_only_fields = fields


class UserDetailSerializer(serializers.ModelSerializer):
    patients = PatientMiniSerializer(source='patient_users', many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'passport', 'department', 'full_name', 'username',
            'phone_number', 'role', 'is_active', 'price', 'patients'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'passport', 'department', 'full_name', 'username',
            'phone_number', 'password', 'role', 'price'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        return UserService.create_user(validated_data)

    def update(self, instance, validated_data):
        return UserService.update_user(instance, validated_data)
