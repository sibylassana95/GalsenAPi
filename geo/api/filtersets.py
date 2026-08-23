import django_filters

from geo.models import Arrondissement, Commune, Departement, Region, Village


class RegionFilterSet(django_filters.FilterSet):
    class Meta:
        model = Region
        fields = ['code_court']


class DepartementFilterSet(django_filters.FilterSet):
    region = django_filters.CharFilter(field_name='region__pcode')

    class Meta:
        model = Departement
        fields = ['region']


class ArrondissementFilterSet(django_filters.FilterSet):
    departement = django_filters.CharFilter(field_name='departement__pcode')

    class Meta:
        model = Arrondissement
        fields = ['departement']


class CommuneFilterSet(django_filters.FilterSet):
    departement = django_filters.CharFilter(field_name='departement__pcode')
    arrondissement = django_filters.CharFilter(field_name='arrondissement__pcode')

    class Meta:
        model = Commune
        fields = ['departement', 'arrondissement', 'type']


class VillageFilterSet(django_filters.FilterSet):
    region = django_filters.CharFilter(field_name='region__pcode')
    commune = django_filters.NumberFilter(field_name='commune_id')

    class Meta:
        model = Village
        fields = ['region', 'commune']
