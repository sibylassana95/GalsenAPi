import json
import requests
from django.shortcuts import render
from rest_framework import generics
from rest_framework.filters import SearchFilter
from django.core.paginator import Paginator
from .models import Arrondissement, Pays, Departements, Regions, Village, Commune, Universites
from .serializers import ArrondissementsSerializer, CommunesSerializer, PaysSerializer, DepartementsSerializer, RegionsSerializer, VillagesSerializer,UniversitesSerializer

def pays_view(request):
    url_pays = "https://raw.githubusercontent.com/sibylassana95/GalsenAPi/refs/heads/main/dataset/senegal.json"
    response = requests.get(url_pays)
    data_pays = json.loads(response.text)

    # Synchroniser les données du pays avec la base de données
    existing_pays_names = set(Pays.objects.values_list('pays', flat=True))
    
    if data_pays['pays'] not in existing_pays_names:
        # Créer une nouvelle instance de Pays si elle n'existe pas déjà
        new_pays = Pays(
            pays=data_pays['pays'],
            capital=data_pays['capital'],
            langueOfficielle=data_pays['langueOfficielle'],
            languesNationales=", ".join(data_pays['languesNationales']),
            monnaie=data_pays['monnaie'],
            devise=data_pays['devise'],
            drapeau=data_pays['drapeau'],
            codeIso=data_pays['codeIso'],
            indicatif=data_pays['indicatif'],
            habitants=data_pays['habitants'],
            surface=data_pays['surface'],
            regions=data_pays['regions'],
            departments=data_pays['departments']
        )
        new_pays.save()  # Enregistrer l'instance dans la base de données

    # Récupérer toutes les données des pays pour affichage
    donne_db = Pays.objects.all()

    return render(request, 'pays.html', {'data': donne_db,'data_pays': data_pays})

def departement_view(request):
    url_departement = "https://raw.githubusercontent.com/sibylassana95/GalsenAPi/refs/heads/main/dataset/departments.json"
    response = requests.get(url_departement)
    data_departement = json.loads(response.text)
    query = request.GET.get('q')
    
    # Synchroniser les données
    for departement in data_departement:
        if not Departements.objects.filter(nom=departement['nom']).exists():
            if 'arrondissements' in departement:
                Departements.objects.create(
                    nom=departement['nom'],
                    region=departement['region'],
                    population=departement['population'],
                    superficie=departement['superficie'],
                    arrondissements=departement['arrondissements']
                )
    
    # Requête avec recherche
    donne_db = Departements.objects.all()
    total_count = donne_db.count()
    if query:
        donne_db = donne_db.filter(nom__icontains=query) | donne_db.filter(region__icontains=query)
    
    # Pagination
    paginator = Paginator(donne_db, 50)  
    page = request.GET.get('page')
    data = paginator.get_page(page)
    
    return render(request, 'departement.html', {
        'data': data,
        'total_count': total_count,
        'query': query
    })

def region_view(request):
    url_region = "https://raw.githubusercontent.com/sibylassana95/GalsenAPi/refs/heads/main/dataset/regions.json"
    response = requests.get(url_region)
    data_region = json.loads(response.text)
    query = request.GET.get('q')
    
    # Synchroniser les données
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
            existing_region_names.add(region['nom'])
    
    if new_regions:
        Regions.objects.bulk_create(new_regions)
    
    # Requête avec recherche
    donnedb = Regions.objects.all()
    total_count = donnedb.count()
    if query:
        donnedb = donnedb.filter(nom__icontains=query) | donnedb.filter(code__icontains=query)
    
    # Pagination
    paginator = Paginator(donnedb, 50)
    page = request.GET.get('page')
    data = paginator.get_page(page)
    
    return render(request, 'region.html', {
        'data': data,
        'total_count': total_count,
        'query': query
    })

def village_view(request):
    url_village = "https://raw.githubusercontent.com/sibylassana95/GalsenAPi/refs/heads/main/dataset/village.json"
    response = requests.get(url_village)
    data_village = json.loads(response.text)
    query = request.GET.get('q')
    
    # Synchroniser les données
    existing_village_names = set(Village.objects.values_list('nom', flat=True))
    new_villages = []
    
    for village in data_village:
        if village['nom'] not in existing_village_names:
            new_villages.append(Village(
                nom=village['nom'],
                region=village['region']
            ))
            existing_village_names.add(village['nom'])
    
    if new_villages:
        Village.objects.bulk_create(new_villages)
    
    # Requête avec recherche
    donne_db = Village.objects.all()
    total_count = donne_db.count()
    if query:
        donne_db = donne_db.filter(nom__icontains=query) | donne_db.filter(region__icontains=query)
    
    # Pagination
    paginator = Paginator(donne_db, 50)  
    page = request.GET.get('page')
    data = paginator.get_page(page)
    
    return render(request, 'village.html', {
        'data': data,
        'total_count': total_count,
        'query': query
    })

def arrondissement_view(request):
    url_arrondissement = "https://raw.githubusercontent.com/sibylassana95/GalsenAPi/refs/heads/main/dataset/arrondissement.json"
    response = requests.get(url_arrondissement)
    data_arrondissement = json.loads(response.text)
    query = request.GET.get('q')
    
    # Synchroniser les données
    existing_arrondissement_names = set(Arrondissement.objects.values_list('nom', flat=True))
    new_arrondissements = []
    
    for arrondissement in data_arrondissement:
        if arrondissement['nom'] not in existing_arrondissement_names:
            new_arrondissements.append(Arrondissement(
                nom=arrondissement['nom'],
                region=arrondissement['region']
            ))
            existing_arrondissement_names.add(arrondissement['nom'])
    
    if new_arrondissements:
        Arrondissement.objects.bulk_create(new_arrondissements)
    
    # Requête avec recherche
    donne_db = Arrondissement.objects.all()
    total_count = donne_db.count()
    if query:
        donne_db = donne_db.filter(nom__icontains=query) | donne_db.filter(region__icontains=query)
    
    # Pagination
    paginator = Paginator(donne_db, 50)
    page = request.GET.get('page')
    data = paginator.get_page(page)
    
    return render(request, 'arrondissement.html', {
        'data': data,
        'total_count': total_count,
        'query': query
    })

def commune_view(request):
    url_commune = "https://raw.githubusercontent.com/sibylassana95/GalsenAPi/refs/heads/main/dataset/commune.json"
    response = requests.get(url_commune)
    data_commune = json.loads(response.text)
    query = request.GET.get('q')
    
    # Synchroniser les données
    existing_commune_names = set(Commune.objects.values_list('nom', flat=True))
    new_communes = []
    
    for commune in data_commune:
        if commune['nom'] not in existing_commune_names:
            new_communes.append(Commune(
                nom=commune['nom'],
                region=commune['region']
            ))
            existing_commune_names.add(commune['nom'])
    
    if new_communes:
        Commune.objects.bulk_create(new_communes)
    
    # Requête avec recherche
    donne_db = Commune.objects.all()
    total_count = donne_db.count()
    
    if query:
        donne_db = donne_db.filter(nom__icontains=query) | donne_db.filter(region__icontains=query)
    
    # Pagination
    paginator = Paginator(donne_db, 50)
    page = request.GET.get('page')
    data = paginator.get_page(page)
    
    return render(request, 'commune.html', {
        'data': data,
        'total_count': total_count,
        'query': query
    })
    
    
    
def universite_view(request):
    url_universite = "https://raw.githubusercontent.com/sibylassana95/GalsenAPi/refs/heads/main/dataset/universite_ecole_formation.json"
    response = requests.get(url_universite)
    data_universite = json.loads(response.text)
    query = request.GET.get('q')
    
    # Synchroniser les données
    existing_universite_names = set(Universites.objects.values_list('nom', flat=True))
    new_universites = []
    
    for universite in data_universite:
        if universite['nom'] not in existing_universite_names:
            new_universites.append(Universites(
                nom=universite['nom'],
                logo=universite['logo'],
            ))
            existing_universite_names.add(universite['nom'])
    
    if new_universites:
        Universites.objects.bulk_create(new_universites)
    
    # Requête avec recherche
    donne_db = Universites.objects.all()
    # Total universités
    total_count = donne_db.count()
    if query:
        donne_db = donne_db.filter(nom__icontains=query)
    
    # Pagination
    paginator = Paginator(donne_db, 21)
    page = request.GET.get('page')
    data = paginator.get_page(page)
    
    return render(request, 'universite.html', {
        'data': data,
        'total_count': total_count,
        'query': query
    })    

# API Views remain unchanged
class PaysList(generics.ListAPIView):
    queryset = Pays.objects.all()
    serializer_class = PaysSerializer
    filter_backends = [SearchFilter]
    search_fields = ['pays', 'capital', 'langueOfficielle', 'monnaie']

class DepartementsList(generics.ListAPIView):
    queryset = Departements.objects.all()
    serializer_class = DepartementsSerializer
    filter_backends = [SearchFilter]
    search_fields = ['nom']

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
    search_fields = ['nom']

class VillageDetail(generics.RetrieveAPIView):
    queryset = Village.objects.all()
    serializer_class = VillagesSerializer

class ArrondissementList(generics.ListAPIView):
    queryset = Arrondissement.objects.all()
    serializer_class = ArrondissementsSerializer
    filter_backends = [SearchFilter]
    search_fields = ['nom']

class ArrondissementDetail(generics.RetrieveAPIView):
    queryset = Arrondissement.objects.all()
    serializer_class = ArrondissementsSerializer
    
class CommuneList(generics.ListAPIView):
    queryset = Commune.objects.all()
    serializer_class = CommunesSerializer
    filter_backends = [SearchFilter]
    search_fields = ['nom']

class CommuneDetail(generics.RetrieveAPIView):
    queryset = Commune.objects.all()
    serializer_class = CommunesSerializer
    

class UniversitesList(generics.ListAPIView):
    queryset = Universites.objects.all()
    serializer_class = UniversitesSerializer
    filter_backends = [SearchFilter]
    search_fields = ['nom']    

class UniversitesDetail(generics.RetrieveAPIView):
    queryset = Universites.objects.all()
    serializer_class = UniversitesSerializer
    