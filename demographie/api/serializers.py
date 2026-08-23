from rest_framework import serializers

from demographie.models import PopulationRecord


class PopulationRecordSerializer(serializers.ModelSerializer):
    """PopulationRecord avec nom/pcode de l'entité et de la région de rattachement.

    Pour entity_type='region', region_pcode/region_nom désignent la région
    elle-même ; pour 'departement', la région parente.
    """

    entite_nom = serializers.SerializerMethodField()
    entite_pcode = serializers.SerializerMethodField()
    region_pcode = serializers.SerializerMethodField()
    region_nom = serializers.SerializerMethodField()

    class Meta:
        model = PopulationRecord
        fields = [
            'id', 'entity_type', 'entite_nom', 'entite_pcode',
            'region_pcode', 'region_nom',
            'annee', 'population', 'hommes', 'femmes', 'value_type',
        ]

    def _entite(self, obj):
        return obj.region if obj.entity_type == 'region' else obj.departement

    def get_entite_nom(self, obj):
        entite = self._entite(obj)
        return entite.nom if entite else None

    def get_entite_pcode(self, obj):
        entite = self._entite(obj)
        return entite.pcode if entite else None

    def get_region_pcode(self, obj):
        return obj.region.pcode if obj.region else None

    def get_region_nom(self, obj):
        return obj.region.nom if obj.region else None
