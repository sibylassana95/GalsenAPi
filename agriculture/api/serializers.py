from rest_framework import serializers

from agriculture.models import Culture, ProductionAgricole


class CultureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Culture
        fields = ['id', 'code_faostat', 'nom']


class ProductionAgricoleSerializer(serializers.ModelSerializer):
    culture_nom = serializers.CharField(source='culture.nom', read_only=True)
    element_display = serializers.CharField(
        source='get_element_display', read_only=True
    )

    class Meta:
        model = ProductionAgricole
        fields = [
            'id', 'culture', 'culture_nom',
            'element', 'element_display', 'annee', 'valeur', 'flag',
        ]
