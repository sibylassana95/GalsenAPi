from rest_framework import serializers

from .models import Pays, Departements, Regions,Village,Arrondissement,Commune,Universites


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


class ArrondissementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Arrondissement
        fields = '__all__'
        

class CommunesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commune
        fields = '__all__'   
        
class UniversitesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Universites
        fields = '__all__'             