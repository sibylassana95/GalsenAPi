import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from agriculture.models import Culture, ProductionAgricole

from .serializers import CultureSerializer, ProductionAgricoleSerializer


class ProductionFilterSet(django_filters.FilterSet):
    culture = django_filters.CharFilter(field_name='culture__code_faostat')
    element = django_filters.ChoiceFilter(
        choices=ProductionAgricole.ELEMENT_CHOICES
    )
    annee_min = django_filters.NumberFilter(field_name='annee', lookup_expr='gte')
    annee_max = django_filters.NumberFilter(field_name='annee', lookup_expr='lte')

    class Meta:
        model = ProductionAgricole
        fields = ['culture', 'element', 'annee_min', 'annee_max']


class CultureViewSet(viewsets.ReadOnlyModelViewSet):
    """Cultures et produits FAOSTAT présents pour le Sénégal."""

    queryset = Culture.objects.all()
    serializer_class = CultureSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nom', 'code_faostat']
    ordering_fields = ['nom', 'code_faostat']
    ordering = ['nom']


class ProductionAgricoleViewSet(viewsets.ReadOnlyModelViewSet):
    """Production agricole FAOSTAT (Sénégal).

    Filtres : ?culture=<code_faostat>, ?element=, ?annee_min=, ?annee_max=.
    """

    queryset = ProductionAgricole.objects.select_related('culture').all()
    serializer_class = ProductionAgricoleSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductionFilterSet
    search_fields = ['culture__nom']
    ordering_fields = ['annee', 'valeur']
    ordering = ['-annee', 'culture__nom']
