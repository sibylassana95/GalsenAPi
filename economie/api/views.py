import django_filters
from django.db.models import Count, Max, OuterRef, Subquery
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from GalsenifyDj.filters import NullsLastOrderingFilter

from economie.models import IndicateurEconomique, ObservationEconomique

from .serializers import (
    IndicateurEconomiqueSerializer,
    ObservationEconomiqueSerializer,
)


class IndicateurEconomiqueViewSet(viewsets.ReadOnlyModelViewSet):
    """Indicateurs économiques World Bank (Sénégal) avec agrégats.

    Filtres : ?categorie=, ?search= (nom / nom officiel / code).
    """

    # Les codes WB contiennent des '.' (NY.GDP.MKTP.CD) : élargit le regex
    # du router pour le détail /economie/indicateurs/{code}/.
    lookup_value_regex = r'[^/]+'
    lookup_field = 'code'
    serializer_class = IndicateurEconomiqueSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, NullsLastOrderingFilter]
    filterset_fields = ['categorie']
    search_fields = ['nom', 'nom_officiel', 'code']
    ordering_fields = ['code', 'nom', 'categorie', 'nb_observations',
                       'derniere_annee']
    ordering = ['categorie', 'code']

    def get_queryset(self):
        derniere = (
            ObservationEconomique.objects
            .filter(indicateur=OuterRef('pk'))
            .order_by('-annee')
        )
        return IndicateurEconomique.objects.select_related('source').annotate(
            nb_observations=Count('observations'),
            derniere_annee=Subquery(derniere.values('annee')[:1]),
            derniere_valeur=Subquery(derniere.values('valeur')[:1]),
        )


class ObservationFilterSet(django_filters.FilterSet):
    indicateur = django_filters.CharFilter(field_name='indicateur__code')
    annee_min = django_filters.NumberFilter(field_name='annee',
                                            lookup_expr='gte')
    annee_max = django_filters.NumberFilter(field_name='annee',
                                            lookup_expr='lte')

    class Meta:
        model = ObservationEconomique
        fields = ['indicateur', 'annee_min', 'annee_max']


class ObservationEconomiqueViewSet(viewsets.ReadOnlyModelViewSet):
    """Observations annuelles des indicateurs économiques.

    Filtres : ?indicateur=<code WB>, ?annee_min=, ?annee_max=.
    Tri : ?ordering=annee|-annee|valeur|-valeur.
    """

    queryset = ObservationEconomique.objects.select_related('indicateur')
    serializer_class = ObservationEconomiqueSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, NullsLastOrderingFilter]
    filterset_class = ObservationFilterSet
    search_fields = ['indicateur__code', 'indicateur__nom']
    ordering_fields = ['annee', 'valeur']
    ordering = ['-annee']
