import django_filters
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from climat.models import ObservationMensuelle, StationClimatique

from .serializers import (
    ObservationMensuelleSerializer,
    StationClimatiqueSerializer,
)


class StationClimatiqueViewSet(viewsets.ReadOnlyModelViewSet):
    """Stations météo GHCN-Daily présentes au Sénégal.

    Filtres : ?search= (nom / station_id).
    """

    lookup_field = 'station_id'
    serializer_class = StationClimatiqueSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nom', 'station_id']
    ordering_fields = ['nom', 'station_id', 'nb_observations']
    ordering = ['nom']

    def get_queryset(self):
        return StationClimatique.objects.annotate(
            nb_observations=Count('observations'),
        )


class ObservationFilterSet(django_filters.FilterSet):
    station = django_filters.CharFilter(field_name='station__station_id')
    annee_min = django_filters.NumberFilter(field_name='annee',
                                             lookup_expr='gte')
    annee_max = django_filters.NumberFilter(field_name='annee',
                                             lookup_expr='lte')

    class Meta:
        model = ObservationMensuelle
        fields = ['station', 'annee_min', 'annee_max', 'mois']


class ObservationMensuelleViewSet(viewsets.ReadOnlyModelViewSet):
    """Agrégats mensuels des stations climatiques (GHCN-Daily).

    Filtres : ?station=<station_id>, ?annee_min=, ?annee_max=, ?mois=.
    Tri : ?ordering=annee|-annee|prcp_mm|-prcp_mm|tavg|mois...
    """

    queryset = (
        ObservationMensuelle.objects.select_related('station')
        .order_by('-annee', '-mois')
    )
    serializer_class = ObservationMensuelleSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ObservationFilterSet
    search_fields = ['station__station_id', 'station__nom']
    ordering_fields = [
        'annee', 'mois', 'tavg', 'tmin', 'tmax', 'prcp_mm', 'nb_jours',
    ]
    ordering = ['-annee', '-mois']
