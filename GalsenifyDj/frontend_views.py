import json

from django.db.models import Count, Max, Sum
from django.shortcuts import render

from agriculture.models import ProductionAgricole
from climat.models import ObservationMensuelle
from datasets.models import Dataset
from economie.models import ObservationEconomique
from geo.models import Arrondissement, Departement, Region, Village


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
