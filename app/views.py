import json

import requests
from django.shortcuts import render
from rest_framework import generics
from rest_framework.filters import SearchFilter
from .models import Arrondissement, Pays, Departements, Regions,Village,Commune
from .serializers import ArrondissementsSerializer, CommunesSerializer, PaysSerializer, DepartementsSerializer, RegionsSerializer,VillagesSerializer

def pays_view(request):
    url_pays = "https://raw.githubusercontent.com/sibylassana95/GalsenAPi/refs/heads/main/dataset/senegal.json"
    response = requests.get(url_pays)
    data_pays = json.loads(response.text)

    return render(request, 'pays.html', {'data_pays': data_pays})


def departement_view(request):
    url_departement = "https://raw.githubusercontent.com/sibylassana95/GalsenAPi/refs/heads/main/dataset/departments.json"
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
    url_region = "https://raw.githubusercontent.com/sibylassana95/GalsenAPi/refs/heads/main/dataset/regions.json"
    response = requests.get(url_region)
    data_region = json.loads(response.text)
    
    query = request.GET.get('q')
    
    # Pré-charger les noms des régions existantes
    existing_region_names = set(Regions.objects.values_list('nom', flat=True))
    
    new_regions = []
    
    for region in data_region:
        if region['nom'] not in existing_region_names:
            new_regions.append(Regions(
                nom=region['nom'],
                code=region['code'],
                population=region['population'],
                superficie=region['superficie'],
                departments=region['departments']
            ))
            existing_region_names.add(region['nom'])  # Ajouter au set pour éviter les doublons
    
    # Créer les nouvelles régions en une seule opération
    if new_regions:
        Regions.objects.bulk_create(new_regions)
    
    # Appliquer le filtre de recherche
    donnedb = Regions.objects.all()
    if query:
        donnedb = donnedb.filter(nom__icontains=query)
    
    return render(request, 'region.html', {'data': donnedb})

def village_view(request):
    url_village = "https://raw.githubusercontent.com/sibylassana95/GalsenAPi/refs/heads/main/dataset/village.json"
    # Charger les données depuis le cache ou directement si non disponible
    # Pour ce faire, vous pouvez utiliser un mécanisme de cache 
    response = requests.get(url_village)
    data_village = json.loads(response.text)
    
    query = request.GET.get('q')
    
    # Pré-charger les noms des villages existants pour une vérification rapide
    existing_village_names = set(Village.objects.values_list('nom', flat=True))
    
    new_villages = []
    
    for village in data_village:
        if village['nom'] not in existing_village_names:
            new_villages.append(Village(
                nom=village['nom'],
                region=village['region']
            ))
            existing_village_names.add(village['nom'])  # Ajouter au set pour éviter les doublons
    
    # Créer les nouveaux villages en une seule opération
    if new_villages:
        Village.objects.bulk_create(new_villages)
    
    # Appliquer le filtre de recherche
    donne_db = Village.objects.all()
    if query:
        donne_db = donne_db.filter(nom__icontains=query)
    
    return render(request, 'village.html', {'data': donne_db})

def arrondissement_view(request):
    url_arrondissement = "https://raw.githubusercontent.com/sibylassana95/GalsenAPi/refs/heads/main/dataset/arrondissement.json"
    # Charger les données depuis le cache ou directement si non disponible
    # Pour ce faire, vous pouvez utiliser un mécanisme de cache 
    response = requests.get(url_arrondissement)
    data_arrondissement = json.loads(response.text)
    
    query = request.GET.get('q')
    
    # Pré-charger les noms des arrondissements existants pour une vérification rapide
    existing_arrondissement_names = set(Arrondissement.objects.values_list('nom', flat=True))
    
    new_arrondissements = []
    
    for arrondissement in data_arrondissement:
        if arrondissement['nom'] not in existing_arrondissement_names:
            new_arrondissements.append(Arrondissement(
                nom=arrondissement['nom'],
                region=arrondissement['region']
            ))
            existing_arrondissement_names.add(arrondissement['nom'])  # Ajouter au set pour éviter les doublons
    
    # Créer les nouveaux arrondissements en une seule opération
    if new_arrondissements:
        Arrondissement.objects.bulk_create(new_arrondissements)
    
    # Appliquer le filtre de recherche
    donne_db = Arrondissement.objects.all()
    if query:
        donne_db = donne_db.filter(nom__icontains=query)
    
    return render(request, 'arrondissement.html', {'data': donne_db})

def commune_view(request):
    url_commune = "https://raw.githubusercontent.com/sibylassana95/GalsenAPi/refs/heads/main/dataset/commune.json"
    # Charger les données depuis le cache ou directement si non disponible
    # Pour ce faire, vous pouvez utiliser un mécanisme de cache 
    response = requests.get(url_commune)
    data_commune = json.loads(response.text)
    
    query = request.GET.get('q')
    
    # Pré-charger les noms des communes existants pour une vérification rapide
    existing_commune_names = set(Commune.objects.values_list('nom', flat=True))
    
    new_communes = []
    
    for commune in data_commune:
        if commune['nom'] not in existing_commune_names:
            new_communes.append(Commune(
                nom=commune['nom'],
                region=commune['region']
            ))
            existing_commune_names.add(commune['nom'])  # Ajouter au set pour éviter les doublons
    
    # Créer les nouveaux communes en une seule opération
    if new_communes:
        Commune.objects.bulk_create(new_communes)
    
    # Appliquer le filtre de recherche
    donne_db = Commune.objects.all()
    if query:
        donne_db = donne_db.filter(nom__icontains=query)
    
    return render(request, 'commune.html', {'data': donne_db})


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

class ArrondissementList(generics.ListAPIView):
    queryset = Arrondissement.objects.all()
    serializer_class = ArrondissementsSerializer
    filter_backends = [SearchFilter]
    search_fields = ['nom', 'region']

class ArrondissementDetail(generics.RetrieveAPIView):
    queryset = Arrondissement.objects.all()
    serializer_class = ArrondissementsSerializer
    
class CommuneList(generics.ListAPIView):
    queryset = Commune.objects.all()
    serializer_class = CommunesSerializer
    filter_backends = [SearchFilter]
    search_fields = ['nom', 'region']

class CommuneDetail(generics.RetrieveAPIView):
    queryset = Commune.objects.all()
    serializer_class = CommunesSerializer    