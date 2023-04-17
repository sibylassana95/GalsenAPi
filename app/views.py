import json

import requests
from django.shortcuts import render
from rest_framework import generics
from rest_framework.filters import SearchFilter

from .models import Pays, Departements, Regions
from .serializers import PaysSerializer, DepartementsSerializer, RegionsSerializer


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
