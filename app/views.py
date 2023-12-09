import json

import requests
from django.core.paginator import Paginator
from django.shortcuts import render
from rest_framework import generics
from rest_framework.filters import SearchFilter

from .models import Pays, Departements, Regions, Village
from .serializers import PaysSerializer, DepartementsSerializer, RegionsSerializer, VillagesSerializer


def pays_view(request):
    url_pays = "https://raw.githubusercontent.com/sibylassana95/galsenify/main/dataset/senegal.json"
    response = requests.get(url_pays)
    data_pays = json.loads(response.text)

    return render(request, 'pays.html', {'data_pays': data_pays})


def departement_view(request):
    url_departement = "https://raw.githubusercontent.com/sibylassana95/galsenify/main/dataset/departments.json"
    response = requests.get(url_departement)
    data_departement = json.loads(response.text)
    query = request.GET.get('q')
    donne_db = Departements.objects.all()
    if query:
        donne_db = donne_db.filter(nom__icontains=query)

    for departement in data_departement:
        if Departements.objects.filter(nom=departement['nom']).exists():
            continue

        if 'arrondissements' in departement:
            departement_obj = Departements.objects.create(
                nom=departement['nom'],
                region=departement['region'],
                population=departement['population'],
                superficie=departement['superficie'],
                arrondissements=departement['arrondissements']
            )

    return render(request, 'departement.html', {'data': donne_db})


def region_view(request):
    url_region = "https://raw.githubusercontent.com/sibylassana95/galsenify/main/dataset/regions.json"
    response = requests.get(url_region)
    data_region = json.loads(response.text)
    query = request.GET.get('q')
    donnedb = Regions.objects.all()
    if query:
        donnedb = donnedb.filter(nom__icontains=query)
    for region in data_region:
        if not Regions.objects.filter(nom=region['nom']).exists():
            region_obj = Regions.objects.create(
                nom=region['nom'],
                code=region['code'],
                population=region['population'],
                superficie=region['superficie'],
                departments=region['departments']
            )

    return render(request, 'region.html', {'data': donnedb})


def village_view(request):
    url_village = "https://raw.githubusercontent.com/sibylassana95/galsenify/main/dataset/village.json"
    response = requests.get(url_village)
    data_village = json.loads(response.text)
    query = request.GET.get('q')
    donne_db = Village.objects.all()
    if query:
        donne_db = donne_db.filter(nom__icontains=query)

    for village in data_village:
        if Village.objects.filter(nom=village['nom']).exists():
            continue

        village_obj = Village.objects.create(
            nom=village['nom'],
            region=village['region']
        )

    paginator = Paginator(donne_db, 10)  # 10 éléments par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'village.html', {'page_obj': page_obj, 'query': query})


class PaysList(generics.ListAPIView):
    queryset = Pays.objects.all()
    serializer_class = PaysSerializer
    filter_backends = [SearchFilter]
    search_fields = ['pays', 'capital', 'langueOfficielle', 'monnaie']


class DepartementsList(generics.ListAPIView):
    queryset = Departements.objects.all()
    serializer_class = DepartementsSerializer
    filter_backends = [SearchFilter]
    search_fields = ['nom', 'region']


class DepartementsDetail(generics.RetrieveAPIView):
    queryset = Departements.objects.all()
    serializer_class = DepartementsSerializer


class RegionsList(generics.ListAPIView):
    queryset = Regions.objects.all()
    serializer_class = RegionsSerializer
    filter_backends = [SearchFilter]
    search_fields = ['nom', 'code']


class RegionsDetail(generics.RetrieveAPIView):
    queryset = Regions.objects.all()
    serializer_class = RegionsSerializer


class VillageList(generics.ListAPIView):
    queryset = Village.objects.all()
    serializer_class = VillagesSerializer
    filter_backends = [SearchFilter]
    search_fields = ['nom', 'region']


class VillageDetail(generics.RetrieveAPIView):
    queryset = Village.objects.all()
    serializer_class = VillagesSerializer
