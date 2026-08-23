import json

from django.db.models import Count, Max, Sum
from django.shortcuts import render

from agriculture.models import ProductionAgricole
from climat.models import ObservationMensuelle
from datasets.models import Dataset
from economie.models import ObservationEconomique
from geo.models import Arrondissement, Commune, Departement, Region, Village


LNG_MIN, LNG_MAX = -17.85, -11.35
LAT_MIN, LAT_MAX = 12.2, 16.7
MAP_W, MAP_H = 800, 430
PAD_X, PAD_TOP, PAD_BOTTOM = 46, 34, 30


def _map_xy(lat, lng):
    x = PAD_X + (lng - LNG_MIN) / (LNG_MAX - LNG_MIN) * (MAP_W - 2 * PAD_X)
    y = PAD_TOP + (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * (MAP_H - PAD_TOP - PAD_BOTTOM)
    return round(x), round(y)


def _population_bucket(population):
    if population is None:
        return "#95d3ba"
    if population >= 2_000_000:
        return "#003527"
    if population >= 1_000_000:
        return "#064e3b"
    if population >= 750_000:
        return "#0b513d"
    if population >= 500_000:
        return "#116149"
    return "#178155"


CATEGORIES_AFFICHEES = [
    ("geographie", "Géographie"),
    ("demographie", "Démographie"),
    ("agriculture", "Agriculture"),
    ("economie", "Économie"),
    ("climat", "Climat"),
    ("education", "Éducation"),
]


def home_view(request):
    regions = Region.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    top_regions = (
        Region.objects.exclude(population__isnull=True)
        .order_by("-population")[:5]
    )
    population_totale = Region.objects.aggregate(t=Sum("population"))["t"]

    regions_carte = []
    for r in regions:
        x, y = _map_xy(float(r.latitude), float(r.longitude))
        regions_carte.append(
            {
                "pcode": r.pcode,
                "nom": r.nom,
                "x": x,
                "y": y,
                "couleur": _population_bucket(r.population),
                "population": r.population,
            }
        )

    datasets_recents = (
        Dataset.objects.filter(is_public=True)
        .select_related("source")
        .prefetch_related("versions")
        .order_by("-last_refreshed")[:6]
    )

    categories = (
        Dataset.objects.filter(is_public=True)
        .values("categorie")
        .annotate(n=Count("id"))
        .order_by("categorie")
    )
    compte_categories = {c["categorie"]: c["n"] for c in categories}

    dernier_annee_agriculture = ProductionAgricole.objects.aggregate(m=Max("annee"))["m"]
    dernier_annee_climat = ObservationMensuelle.objects.aggregate(m=Max("annee"))["m"]
    dernier_annee_economie = ObservationEconomique.objects.aggregate(m=Max("annee"))["m"]
    nb_datasets = Dataset.objects.filter(is_public=True).count()

    contexte = {
        "stats_geo": {
            "regions": Region.objects.count(),
            "departements": Departement.objects.count(),
            "arrondissements": Arrondissement.objects.count(),
            "villages": Village.objects.count(),
        },
        "population_totale": population_totale,
        "top_regions": top_regions,
        "regions_carte": regions_carte,
        "carte_svg": {"w": MAP_W, "h": MAP_H},
        "datasets_recents": datasets_recents,
        "nb_datasets": nb_datasets,
        "categories_affichees": [
            {"slug": slug, "label": label, "n": compte_categories.get(slug, 0)}
            for slug, label in CATEGORIES_AFFICHEES
        ],
        "compte_categories": compte_categories,
        "fraicheur": {
            "demographie": 2023,
            "agriculture": dernier_annee_agriculture,
            "economie": dernier_annee_economie,
            "climat": dernier_annee_climat,
        },
    }
    return render(request, "home.html", contexte)


def donnees_view(request):
    qs = (
        Dataset.objects.filter(is_public=True)
        .select_related("source")
        .prefetch_related("versions")
    )

    categorie = request.GET.get("categorie", "")
    recherche = request.GET.get("q", "")

    categories_valides = [c for c, _ in Dataset.CATEGORIE_CHOICES]
    if categorie in categories_valides:
        qs = qs.filter(categorie=categorie)
    elif categorie:
        categorie = ""
    if recherche:
        from django.db.models import Q

        qs = qs.filter(Q(titre__icontains=recherche) | Q(description__icontains=recherche))

    datasets = qs.order_by("-last_refreshed")

    totaux_par_categorie = {
        c["categorie"]: c["n"]
        for c in Dataset.objects.filter(is_public=True).values("categorie").annotate(n=Count("id"))
    }
    total_datasets = sum(totaux_par_categorie.values())

    return render(
        request,
        "explorateur.html",
        {
            "datasets": datasets,
            "categories_affichees": [
                {"slug": slug, "label": label, "n": totaux_par_categorie.get(slug, 0)}
                for slug, label in CATEGORIES_AFFICHEES
            ],
            "totaux_par_categorie": totaux_par_categorie,
            "total_datasets": total_datasets,
            "categorie_active": categorie,
            "recherche": recherche,
        },
    )


def _densite(population, superficie):
    if not population or not superficie:
        return None
    return round(population / superficie, 1)


def regions_liste_view(request):
    recherche = request.GET.get("q", "").strip()
    regions = Region.objects.exclude(population__isnull=True).order_by("-population")
    if recherche:
        regions = regions.filter(nom__icontains=recherche)
    regions = [
        {
            "obj": r,
            "densite": _densite(r.population, r.superficie_km2),
            "nb_departements": Departement.objects.filter(region=r).count(),
            "nb_villages": r.villages.count(),
        }
        for r in regions
    ]
    return render(
        request,
        "regions_liste.html",
        {"regions": regions, "recherche": recherche},
    )


def region_detail_view(request, pcode):
    from django.shortcuts import get_object_or_404

    region = get_object_or_404(Region, pcode=pcode)
    departements = (
        Departement.objects.filter(region=region)
        .order_by("-population", "nom")
    )
    departements_ctx = [
        {
            "obj": d,
            "densite": _densite(d.population, d.superficie_km2),
        }
        for d in departements
    ]
    contexte = {
        "region": region,
        "departements": departements_ctx,
        "nb_departements": len(departements_ctx),
        "nb_arrondissements": Arrondissement.objects.filter(departement__region=region).count(),
        "nb_communes": Commune.objects.filter(departement__region=region).count(),
        "nb_villages": region.villages.count(),
        "densite": _densite(region.population, region.superficie_km2),
        "geometry_url": f"/api/v1/regions/{region.pcode}/geometry/",
    }
    return render(request, "region_detail.html", contexte)


def departement_detail_view(request, pcode):
    from django.shortcuts import get_object_or_404

    departement = get_object_or_404(
        Departement.objects.select_related("region"), pcode=pcode
    )
    arrondissements = Arrondissement.objects.filter(departement=departement).order_by("nom")
    communes = Commune.objects.filter(departement=departement).order_by("nom")
    contexte = {
        "departement": departement,
        "region": departement.region,
        "arrondissements": arrondissements,
        "communes": communes,
        "nb_arrondissements": arrondissements.count(),
        "nb_communes": communes.count(),
        "densite": _densite(departement.population, departement.superficie_km2),
        "geometry_url": f"/api/v1/departements/{departement.pcode}/geometry/",
    }
    return render(request, "departement_detail.html", contexte)
