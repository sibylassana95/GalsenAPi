from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.negotiation import BaseContentNegotiation
from rest_framework.response import Response

from datasets.exporters import build_download
from datasets.models import DataSource, Dataset

from .serializers import DataSourceSerializer, DatasetDetailSerializer, DatasetListSerializer


class DownloadContentNegotiation(BaseContentNegotiation):
    def select_parser(self, request, parsers):
        return parsers[0] if parsers else None

    def select_renderer(self, request, renderers, format_suffix=None):
        return renderers[0], renderers[0].media_type


class DatasetViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['categorie', 'source__slug']
    search_fields = ['titre', 'slug', 'description']
    ordering_fields = ['titre', 'last_refreshed']
    ordering = ['titre']

    def initialize_request(self, request, *args, **kwargs):
        match = getattr(request, 'resolver_match', None)
        if match and getattr(match, 'url_name', '') == 'datasets-download':
            self.content_negotiation_class = DownloadContentNegotiation
        return super().initialize_request(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Dataset.objects.filter(is_public=True)
            .select_related('source')
            .prefetch_related('versions')
        )

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DatasetDetailSerializer
        return DatasetListSerializer

    @action(detail=False, methods=['get'], url_path='sources')
    def sources(self, request):
        sources = DataSource.objects.all()
        serializer = DataSourceSerializer(sources, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, slug=None):
        dataset = self.get_object()
        fmt = request.query_params.get('format', '').lower()
        if fmt not in dataset.export_formats:
            formats = ', '.join(dataset.export_formats)
            return Response(
                {'detail': f"Format '{fmt}' non supporté pour ce dataset. Formats disponibles : {formats}."},
                status=400,
            )
        response = build_download(dataset, fmt)
        if response is None:
            return Response(
                {'detail': f"Aucun exporteur disponible pour ce dataset en format '{fmt}'."},
                status=400,
            )
        return response
