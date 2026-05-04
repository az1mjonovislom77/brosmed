from rest_framework import serializers
from doctor.models import Consultations


class ConsultationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultations
        fields = ['id', 'user', 'patient', 'diagnosis', 'recommendation', 'recipe', 'patient_status']


class ConsultationDetailInputSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(required=True)
