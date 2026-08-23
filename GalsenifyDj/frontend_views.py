from django.db.models import Avg, Count, Max, Min, Sum
from django.shortcuts import render

from agriculture.models import Culture, ProductionAgricole
from climat.models import ObservationMensuelle, StationClimatique
from datasets.models import Dataset
from economie.models import ObservationEconomique
from geo.models import Arrondissement, Commune, Departement, Region, Village


CATEGORIES_AFFICHEES = [
    ("geographie", "Géographie"),
    ("demographie", "Démographie"),
    ("agriculture", "Agriculture"),
    ("economie", "Économie"),
    ("climat", "Climat"),
    ("education", "Éducation"),
]


def home_view(request):
    top_regions = (
        Region.objects.exclude(population__isnull=True)
        .order_by("-population")[:5]
    )
    population_totale = Region.objects.aggregate(t=Sum("population"))["t"]

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
    """Hub : chaque domaine pointe vers sa page de données réelles."""
    from datasets.models import Dataset as _Dataset

    domains = [
        {
            "slug": "geographie",
            "label": "Géographie",
            "description": "14 régions, 46 départements, 125 arrondissements, communes et 8 635 villages.",
            "url": "/donnees/geographie/",
            "cta": "Explorer les territoires",
            "stats": [
                ("Régions", Region.objects.count()),
                ("Départements", Departement.objects.count()),
                ("Villages", Village.objects.count()),
            ],
        },
        {
            "slug": "demographie",
            "label": "Démographie",
            "description": "Population officielle RGPH-5 2023 (ANSD) par région et par département, avec répartition hommes / femmes.",
            "url": "/demographie/",
            "cta": "Tableau de bord",
            "stats": [("Population", 18_126_388), ("Régions couvertes", 14), ("Départements", 46)],
        },
        {
            "slug": "agriculture",
            "label": "Agriculture",
            "description": "Productions, superficies et rendements par culture de 1961 à 2024 (FAOSTAT).",
            "url": "/agriculture/",
            "cta": "Tableau de bord",
            "stats": [("Cultures", Culture.objects.count()), ("Observations", ProductionAgricole.objects.count()), ("Années", 64)],
        },
        {
            "slug": "climat",
            "label": "Climat",
            "description": "Températures et précipitations mensuelles de 14 stations GHCN (NOAA), 1950 à 2025.",
            "url": "/climat/",
            "cta": "Tableau de bord",
            "stats": [("Stations", StationClimatique.objects.count()), ("Mois-station", ObservationMensuelle.objects.count()), ("Années", 76)],
        },
        {
            "slug": "economie",
            "label": "Économie",
            "description": "21 indicateurs macroéconomiques de la Banque mondiale, 1960 à 2025.",
            "url": "/economie/",
            "cta": "Tableau de bord",
            "stats": [("Indicateurs", ObservationEconomique.objects.values("indicateur").distinct().count()), ("Observations", ObservationEconomique.objects.count()), ("Années", 66)],
        },
        {
            "slug": "education",
            "label": "Éducation",
            "description": "Établissements d'enseignement supérieur et de formation référencés (source communautaire).",
            "url": "/education/",
            "cta": "Voir les établissements",
            "stats": [("Établissements", _nb_universites())],
        },
    ]

    datasets = (
        _Dataset.objects.filter(is_public=True)
        .select_related("source")
        .order_by("categorie", "titre")
    )

    return render(
        request,
        "donnees.html",
        {"domains": domains, "datasets": datasets},
    )


def _nb_universites():
    from app.models import Universites

    return Universites.objects.count()


ENTITES_GEO = {
    "region": {
        "label": "Régions",
        "search_label": "Rechercher une région…",
    },
    "departement": {"label": "Départements", "search_label": "Rechercher un département…"},
    "arrondissement": {"label": "Arrondissements", "search_label": "Rechercher un arrondissement…"},
    "commune": {"label": "Communes", "search_label": "Rechercher une commune…"},
    "village": {"label": "Villages", "search_label": "Rechercher un village…"},
}


def geographie_view(request):
    from django.core.paginator import Paginator

    entite = request.GET.get("entite", "region")
    if entite not in ENTITES_GEO:
        entite = "region"
    recherche = request.GET.get("q", "").strip()

    configs = {
        "region": Region.objects.all(),
        "departement": Departement.objects.select_related("region"),
        "arrondissement": Arrondissement.objects.select_related("departement", "departement__region"),
        "commune": Commune.objects.select_related("departement", "departement__region"),
        "village": Village.objects.select_related("region", "commune"),
    }
    qs = configs[entite]
    if recherche:
        qs = qs.filter(nom__icontains=recherche)
    qs = qs.order_by("nom")

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page"))

    comptages = {k: v.count() for k, v in configs.items()}
    entites_list = [
        {
            "slug": slug,
            "label": conf["label"],
            "n": comptages[slug],
            "placeholder": conf["search_label"],
        }
        for slug, conf in ENTITES_GEO.items()
    ]
    return render(
        request,
        "geographie.html",
        {
            "entite": entite,
            "entites_list": entites_list,
            "comptages": comptages,
            "page_obj": page,
            "recherche": recherche,
            "entite_placeholder": ENTITES_GEO[entite]["search_label"],
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
