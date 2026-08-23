from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from geo import search as search_service
from geo import statistics as statistics_service
from geo.models import Arrondissement, Commune, Departement, Pays, Region, Village

from .filtersets import (
    ArrondissementFilterSet,
    CommuneFilterSet,
    DepartementFilterSet,
    RegionFilterSet,
    VillageFilterSet,
)
from .serializers import (
    ArrondissementSerializer,
    CommuneSerializer,
    DepartementDetailSerializer,
    DepartementListSerializer,
    PaysSerializer,
    RegionDetailSerializer,
    RegionListSerializer,
    VillageSerializer,
)


def _feature_collection(features):
    return Response({'type': 'FeatureCollection', 'features': features})


class PaysDetailView(RetrieveAPIView):
    queryset = Pays.objects.all()
    serializer_class = PaysSerializer

    def get_object(self):
        pays = self.get_queryset().filter(code_iso2='SN').first()
        if pays is None:
            raise Http404('Aucun pays avec code_iso2 SN.')
        return pays


@method_decorator(cache_page(1800), name='geojson')
@method_decorator(cache_page(1800), name='geometry')
class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'pcode'
    lookup_value_regex = r'(?!geojson$)[^/.]+'
    filterset_class = RegionFilterSet
    search_fields = ['nom']
    ordering_fields = ['nom', 'population', 'superficie_km2']
    ordering = ['nom']

    def get_queryset(self):
        if self.action == 'retrieve':
            return Region.objects.prefetch_related('departements')
        if self.action == 'geojson':
            return Region.objects.order_by('pcode')
        return Region.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RegionDetailSerializer
        return RegionListSerializer

    @action(detail=False, methods=['get'], url_path='geojson')
    def geojson(self, request):
        features = []
        for region in self.filter_queryset(self.get_queryset()):
            if not region.geometry:
                continue
            features.append({
                'type': 'Feature',
                'geometry': region.geometry,
                'properties': {
                    'pcode': region.pcode,
                    'nom': region.nom,
                    'code_court': region.code_court,
                    'chef_lieu': region.chef_lieu,
                    'population': region.population,
                    'superficie_km2': region.superficie_km2,
                },
            })
        return _feature_collection(features)

    @action(detail=True, methods=['get'], url_path='geometry')
    def geometry(self, request, pcode=None):
        region = self.get_object()
        if not region.geometry:
            return Response({'detail': 'Géométrie indisponible pour cette région.'}, status=404)
        return Response({
            'type': 'Feature',
            'geometry': region.geometry,
            'properties': {
                'pcode': region.pcode,
                'nom': region.nom,
                'code_court': region.code_court,
                'chef_lieu': region.chef_lieu,
                'population': region.population,
                'superficie_km2': region.superficie_km2,
            },
        })


@method_decorator(cache_page(1800), name='geojson')
@method_decorator(cache_page(1800), name='geometry')
class DepartementViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'pcode'
    lookup_value_regex = r'(?!geojson$)[^/.]+'
    filterset_class = DepartementFilterSet
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nom']
    ordering_fields = ['nom', 'population', 'superficie_km2']
    ordering = ['nom']

    def get_queryset(self):
        if self.action == 'retrieve':
            return Departement.objects.prefetch_related('arrondissements', 'communes')
        if self.action == 'geojson':
            return Departement.objects.select_related('region').order_by('pcode')
        return Departement.objects.select_related('region')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DepartementDetailSerializer
        return DepartementListSerializer

    @action(detail=False, methods=['get'], url_path='geojson')
    def geojson(self, request):
        features = []
        for departement in self.filter_queryset(self.get_queryset()):
            if not departement.geometry:
                continue
            features.append({
                'type': 'Feature',
                'geometry': departement.geometry,
                'properties': {
                    'pcode': departement.pcode,
                    'nom': departement.nom,
                    'region': departement.region.pcode,
                },
            })
        return _feature_collection(features)

    @action(detail=True, methods=['get'], url_path='geometry')
    def geometry(self, request, pcode=None):
        departement = self.get_object()
        if not departement.geometry:
            return Response({'detail': 'Géométrie indisponible pour ce département.'}, status=404)
        return Response({
            'type': 'Feature',
            'geometry': departement.geometry,
            'properties': {
                'pcode': departement.pcode,
                'nom': departement.nom,
                'region': departement.region.pcode,
            },
        })


class ArrondissementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Arrondissement.objects.select_related('departement')
    serializer_class = ArrondissementSerializer
    lookup_field = 'pcode'
    filterset_class = ArrondissementFilterSet
    search_fields = ['nom']
    ordering_fields = ['nom']
    ordering = ['nom']


class CommuneViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Commune.objects.select_related('departement', 'arrondissement')
    serializer_class = CommuneSerializer
    filterset_class = CommuneFilterSet
    search_fields = ['nom']
    ordering_fields = ['nom', 'population']
    ordering = ['nom']


class VillageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Village.objects.select_related('commune', 'region')
    serializer_class = VillageSerializer
    filterset_class = VillageFilterSet
    search_fields = ['nom']
    ordering_fields = ['nom', 'population']
    ordering = ['nom']


class SearchView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'q', openapi.IN_QUERY, description="Terme recherché (2 caractères minimum)",
                type=openapi.TYPE_STRING, required=True,
            ),
            openapi.Parameter(
                'types', openapi.IN_QUERY,
                description=(
                    'Liste CSV parmi : region,departement,arrondissement,'
                    'commune,village,universite,dataset'
                ),
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                'limit', openapi.IN_QUERY,
                description='Résultats maximum par type (20 par défaut, 50 max)',
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={200: 'Résultats de recherche multi-entités', 400: 'Requête invalide'},
    )
    def get(self, request):
        q = request.query_params.get('q', '')
        if len(q.strip()) < 2:
            return Response(
                {
                    'detail': "Paramètre 'q' requis : termenez avec au moins "
                              '2 caractères.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            types = search_service.parse_types(request.query_params.get('types'))
            limit = search_service.parse_limit(request.query_params.get('limit'))
        except search_service.SearchValidationError as error:
            return Response({'detail': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        results = search_service.search(q, types=types, limit=limit)
        return Response({'count': len(results), 'results': results})


@method_decorator(cache_page(600), name='get')
class StatisticsView(APIView):
    @swagger_auto_schema(responses={200: 'Statistiques globales'})
    def get(self, request):
        return Response(statistics_service.build_statistics())


@method_decorator(cache_page(600), name='get')
class RegionStatisticsView(APIView):
    @swagger_auto_schema(responses={200: 'Statistiques régionales', 404: 'Région inconnue'})
    def get(self, request, pcode):
        stats = statistics_service.region_statistics(pcode)
        if stats is None:
            return Response(
                {'detail': f"Aucune région avec le pcode '{pcode}'."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(stats)
