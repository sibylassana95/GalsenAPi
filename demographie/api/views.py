from django.http import Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework.exceptions import ValidationError
from GalsenifyDj.filters import NullsLastOrderingFilter
from rest_framework.generics import ListAPIView

from demographie.models import PopulationRecord
from geo.models import Region

from .serializers import PopulationRecordSerializer

NIVEAUX = {'region', 'departement'}


class PopulationListView(ListAPIView):
    """Effectifs de population (RGPH-5 2023) par région ou département.

    Filtres : ?niveau=region|departement, ?region=<pcode>, ?annee=<année>.
    """

    serializer_class = PopulationRecordSerializer
    filter_backends = [NullsLastOrderingFilter]
    ordering_fields = ['annee', 'population']
    ordering = ['-annee', '-population']

    def get_queryset(self):
        queryset = PopulationRecord.objects.select_related('region', 'departement')
        params = self.request.query_params

        niveau = params.get('niveau')
        if niveau is not None:
            if niveau not in NIVEAUX:
                raise ValidationError(
                    {"niveau": "Valeur invalide : choisir parmi region, departement."}
                )
            queryset = queryset.filter(entity_type=niveau)

        pcode = params.get('region')
        if pcode is not None:
            if not Region.objects.filter(pcode=pcode).exists():
                raise Http404(f"Aucune région avec le pcode '{pcode}'.")
            queryset = queryset.filter(region__pcode=pcode)

        annee = params.get('annee')
        if annee is not None:
            if not annee.isdigit():
                raise ValidationError({"annee": "Année invalide : entier attendu."})
            queryset = queryset.filter(annee=int(annee))

        return queryset

    @swagger_auto_schema(
        responses={200: 'Effectifs de population', 400: 'Requête invalide',
                   404: 'Région inconnue'}
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
