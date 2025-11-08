from rest_framework import serializers
from user.models import User
from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['department', 'full_name', 'username', 'phone_number', 'password', 'role', 'is_active']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class SignInSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')

        user = authenticate(phone_number=phone_number, password=password)
        if user is None:
            raise ValidationError("Invalid phone number or password.")

        data['user'] = user
        return data
