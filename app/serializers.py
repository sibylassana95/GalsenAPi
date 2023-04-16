from rest_framework import serializers

from .models import Pays, Departements, Regions


class PaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pays
        fields = '__all__'


class DepartementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departements
        fields = '__all__'


class RegionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Regions
        fields = '__all__'
