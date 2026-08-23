from rest_framework import serializers

from economie.models import IndicateurEconomique, ObservationEconomique


class IndicateurEconomiqueSerializer(serializers.ModelSerializer):
    nb_observations = serializers.IntegerField(read_only=True)
    derniere_annee = serializers.IntegerField(
        allow_null=True, read_only=True
    )
    derniere_valeur = serializers.DecimalField(
        max_digits=24, decimal_places=6, allow_null=True, read_only=True,
    )

    class Meta:
        model = IndicateurEconomique
        fields = [
            'code', 'nom', 'nom_officiel', 'categorie', 'unite',
            'nb_observations', 'derniere_annee', 'derniere_valeur',
        ]


class ObservationEconomiqueSerializer(serializers.ModelSerializer):
    indicateur = serializers.CharField(source='indicateur.code', read_only=True)
    indicateur_nom = serializers.CharField(
        source='indicateur.nom', read_only=True
    )
    unite = serializers.CharField(source='indicateur.unite', read_only=True)

    class Meta:
        model = ObservationEconomique
        fields = [
            'id', 'indicateur', 'indicateur_nom', 'unite', 'annee', 'valeur',
        ]
