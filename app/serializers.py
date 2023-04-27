from rest_framework import serializers

from .models import Pays, Departements, Regions,Village


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

class VillagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Village
        fields = '__all__'        
