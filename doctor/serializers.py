from rest_framework import serializers

from .models import Consultations


class ConsultationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultations
        fields = ['id', 'user', 'patient', 'diagnosis', 'diagnosis_uz', 'diagnosis_ru', 'recommendation',
                  'recommendation_uz', 'recommendation_ru', 'recipe', 'recipe_uz', 'recipe_ru', 'patient_status']
