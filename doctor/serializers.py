from rest_framework import serializers

from .models import Consultations


class ConsultationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultations
        fields = ['id', 'user', 'patient', 'diagnosis', 'recommendation', 'recipe', 'patient_status']
