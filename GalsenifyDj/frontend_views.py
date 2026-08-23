import json

from django.db.models import Avg, Count, Max, Min, Sum
from django.shortcuts import render

from agriculture.models import Culture, ProductionAgricole
from climat.models import ObservationMensuelle, StationClimatique
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


# ---------------------------------------------------------------------------
# Dashboards par domaine (Phase 7d)
# ---------------------------------------------------------------------------

def demographie_dashboard(request):
    from demographie.models import PopulationRecord

    regions = Region.objects.exclude(population__isnull=True).order_by("-population")
    totaux = regions.aggregate(t=Sum("population"))
    repartition = PopulationRecord.objects.filter(
        entity_type="region", annee=2023
    ).select_related("region").order_by("-population")

    regions_ctx = [
        {
            "nom": r.nom,
            "pcode": r.pcode,
            "population": r.population,
            "densite": _densite(r.population, r.superficie_km2),
        }
        for r in regions
    ]
    hommes_total = sum((p.hommes or 0) for p in repartition)
    femmes_total = sum((p.femmes or 0) for p in repartition)
    top_departements = [
        {
            "nom": d.nom,
            "pcode": d.pcode,
            "region": d.region.nom,
            "population": d.population,
        }
        for d in Departement.objects.exclude(population__isnull=True)
        .select_related("region").order_by("-population")[:5]
    ]
    return render(
        request,
        "dashboard_demographie.html",
        {
            "population_totale": totaux["t"],
            "hommes_total": hommes_total,
            "femmes_total": femmes_total,
            "regions": regions_ctx,
            "repartition": [
                {
                    "nom": p.region.nom,
                    "hommes": p.hommes,
                    "femmes": p.femmes,
                    "population": p.population,
                }
                for p in repartition
            ],
            "top_departements": top_departements,
        },
    )


def agriculture_dashboard(request):
    periode = ProductionAgricole.objects.aggregate(
        debut=Min("annee"), fin=Max("annee")
    )
    nb_cultures = Culture.objects.count()
    nb_records = ProductionAgricole.objects.count()

    evolution = (
        ProductionAgricole.objects
        .filter(element="production_tonnes", culture__code_faostat__lt=1700)
        .values("annee")
        .annotate(total=Sum("valeur"))
        .order_by("annee")
    )
    top_2024 = list(
        ProductionAgricole.objects
        .filter(annee=2024, element="production_tonnes", culture__code_faostat__lt=1700)
        .select_related("culture")
        .order_by("-valeur")[:10]
    )
    rendement_arachide = (
        ProductionAgricole.objects
        .filter(culture__code_faostat="242", element="rendement")
        .order_by("annee")
    )
    superficie_arachide = (
        ProductionAgricole.objects
        .filter(culture__code_faostat="242", element="superficie_ha")
        .order_by("annee")
    )
    return render(
        request,
        "dashboard_agriculture.html",
        {
            "periode": periode,
            "nb_cultures": nb_cultures,
            "nb_records": nb_records,
            "evolution": [
                {"annee": e["annee"], "total": float(e["total"])} for e in evolution
            ],
            "top_2024": top_2024,
            "top_2024_data": [
                {"culture": p.culture.nom, "valeur": float(p.valeur)}
                for p in top_2024
            ],
            "rendement_arachide": [
                {"annee": r.annee, "valeur": float(r.valeur)} for r in rendement_arachide
            ],
            "superficie_arachide": [
                {"annee": r.annee, "valeur": float(r.valeur)} for r in superficie_arachide
            ],
        },
    )


def climat_dashboard(request):
    stations = StationClimatique.objects.order_by("nom")
    nb_mois = ObservationMensuelle.objects.count()
    periode = ObservationMensuelle.objects.aggregate(
        debut=Min("annee"), fin=Max("annee")
    )
    brut = (
        ObservationMensuelle.objects
        .values("annee")
        .annotate(
            tavg=Avg("tavg"),
            precip_totale=Sum("prcp_mm"),
            nb_stations=Count("station", distinct=True),
        )
        .order_by("annee")
    )
    serie = [
        {
            "annee": b["annee"],
            "tavg": round(float(b["tavg"]), 2) if b["tavg"] is not None else None,
            "precip_moyenne": round(float(b["precip_totale"]) / b["nb_stations"], 1)
            if b["precip_totale"] is not None else None,
            "nb_stations": b["nb_stations"],
        }
        for b in brut
        if b["nb_stations"] >= 5
    ]
    return render(
        request,
        "dashboard_climat.html",
        {
            "stations": stations,
            "nb_stations": stations.count(),
            "nb_mois": nb_mois,
            "periode": periode,
            "serie": serie,
            "seuil_stations": 5,
        },
    )


def economie_dashboard(request):
    from economie.models import IndicateurEconomique

    indicateurs = IndicateurEconomique.objects.order_by("categorie", "nom")
    indicateurs_ctx = []
    for ind in indicateurs:
        derniere = ind.observations.order_by("-annee").first()
        indicateurs_ctx.append(
            {
                "obj": ind,
                "derniere_valeur": derniere.valeur if derniere else None,
                "derniere_annee": derniere.annee if derniere else None,
            }
        )

    def _serie(code):
        return list(
            ObservationEconomique.objects
            .filter(indicateur__code=code)
            .order_by("annee")
            .values_list("annee", "valeur")
        )

    pib = _serie("NY.GDP.MKTP.CD")
    croissance = _serie("NY.GDP.MKTP.KD.ZG")
    inflation = _serie("FP.CPI.TOTL.ZG")

    def _derniere(serie):
        return {"annee": serie[-1][0], "valeur": serie[-1][1]} if serie else None

    return render(
        request,
        "dashboard_economie.html",
        {
            "indicateurs": indicateurs_ctx,
            "pib": [(a, float(v)) for a, v in pib],
            "croissance": [(a, float(v)) for a, v in croissance],
            "inflation": [(a, float(v)) for a, v in inflation],
            "pib_kpi": _derniere(pib),
            "croissance_kpi": _derniere(croissance),
            "inflation_kpi": _derniere(inflation),
        },
    )


def education_page(request):
    from app.models import Universites

    recherche = request.GET.get("q", "").strip()
    universites = Universites.objects.order_by("nom")
    if recherche:
        universites = universites.filter(nom__icontains=recherche)
    return render(
        request,
        "education.html",
        {"universites": universites, "recherche": recherche,
         "total": Universites.objects.count()},
    )


def developers_page(request):
    return render(request, "developers.html", {})
