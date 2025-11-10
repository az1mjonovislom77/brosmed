from rest_framework import serializers

from utils.models import ClinicAbout


class ClinicAboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicAbout
        fields = '__all__'
