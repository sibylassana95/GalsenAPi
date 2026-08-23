from rest_framework import serializers

from geo.models import (
    Arrondissement,
    Commune,
    Departement,
    Pays,
    Region,
    Village,
)


class PaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pays
        fields = [
            'id', 'nom', 'code_iso2', 'capitale', 'indicatif',
            'monnaie', 'devise', 'population', 'superficie_km2',
        ]
        ref_name = 'Pays'


class DepartementMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departement
        fields = ['pcode', 'nom']


class ArrondissementMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Arrondissement
        fields = ['pcode', 'nom']


class CommuneMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commune
        fields = ['id', 'nom', 'type']


class RegionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = [
            'pcode', 'nom', 'code_court', 'chef_lieu',
            'population', 'superficie_km2', 'latitude', 'longitude',
        ]


class RegionDetailSerializer(RegionListSerializer):
    departements = DepartementMinimalSerializer(many=True, read_only=True)

    class Meta(RegionListSerializer.Meta):
        fields = RegionListSerializer.Meta.fields + ['departements']


class DepartementListSerializer(serializers.ModelSerializer):
    region = serializers.SlugRelatedField(slug_field='pcode', read_only=True)

    class Meta:
        model = Departement
        fields = [
            'pcode', 'nom', 'region', 'population', 'superficie_km2',
            'latitude', 'longitude',
        ]


class DepartementDetailSerializer(DepartementListSerializer):
    arrondissements = ArrondissementMinimalSerializer(many=True, read_only=True)
    communes = CommuneMinimalSerializer(many=True, read_only=True)

    class Meta(DepartementListSerializer.Meta):
        fields = DepartementListSerializer.Meta.fields + [
            'arrondissements', 'communes',
        ]


class ArrondissementSerializer(serializers.ModelSerializer):
    departement = serializers.SlugRelatedField(slug_field='pcode', read_only=True)

    class Meta:
        model = Arrondissement
        fields = ['pcode', 'nom', 'departement', 'latitude', 'longitude']


class CommuneSerializer(serializers.ModelSerializer):
    departement = serializers.SlugRelatedField(slug_field='pcode', read_only=True)
    arrondissement = serializers.SlugRelatedField(
        slug_field='pcode', read_only=True, allow_null=True
    )

    class Meta:
        model = Commune
        fields = ['id', 'nom', 'type', 'departement', 'arrondissement']


class VillageSerializer(serializers.ModelSerializer):
    region = serializers.SlugRelatedField(slug_field='pcode', read_only=True)
    commune = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    class Meta:
        model = Village
        fields = ['id', 'nom', 'region', 'commune', 'latitude', 'longitude']
