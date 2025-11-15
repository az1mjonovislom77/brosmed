from rest_framework import serializers

from utils.models import ClinicAbout


class ClinicAboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicAbout
        fields = '__all__'


class ClinicStatsSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    jami_bemorlar = serializers.IntegerField()
    konsultatsiyalar = serializers.IntegerField()
    tahlillar = serializers.IntegerField()
    tolovlar = serializers.FloatField()


class ClinicStatsInputSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
