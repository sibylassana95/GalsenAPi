from django.db.models import Count, Sum
from django.utils import timezone

from app.models import Universites
from datasets.models import Dataset
from geo.models import Arrondissement, Commune, Departement, Region, Village

POPULATION_SOURCE_NOTE = (
    "Chiffres hérités du dataset Galsenify (base ANSD) — RGPH-5 2023 à intégrer"
)


def _densite(population, superficie):
    if population is None or superficie is None:
        return None
    superficie = float(superficie)
    if superficie == 0:
        return None
    return round(float(population) / superficie, 1)


def _region_summary(region):
    superficie = float(region.superficie_km2) if region.superficie_km2 is not None else None
    return {
        'pcode': region.pcode,
        'nom': region.nom,
        'population': region.population,
        'superficie_km2': superficie,
        'densite': _densite(region.population, superficie),
    }


def build_statistics():
    regions = Region.objects.all()
    counts = {
        'regions': regions.count(),
        'departements': Departement.objects.count(),
        'arrondissements': Arrondissement.objects.count(),
        'communes': Commune.objects.count(),
        'villages': Village.objects.count(),
    }

    population_totale = regions.aggregate(total=Sum('population'))['total'] or 0
    superficie_totale = float(
        regions.aggregate(total=Sum('superficie_km2'))['total'] or 0
    )

    par_region = [
        _region_summary(region)
        for region in regions.filter(population__isnull=False).order_by('-population')
    ]

    plus_peuplee = par_region[0] if par_region else None

    denses = [row for row in par_region if row['densite'] is not None]
    plus_dense = None
    if denses:
        plus_dense = sorted(
            denses, key=lambda row: (-row['densite'], row['nom'].casefold())
        )[0]

    par_categorie = dict(
        Dataset.objects.filter(is_public=True)
        .values('categorie')
        .annotate(total=Count('id'))
        .values_list('categorie', 'total')
    )

    return {
        'geographie': {
            **counts,
            'entites_georeferencees': (
                counts['regions'] + counts['departements'] + counts['arrondissements']
            ),
        },
        'population': {
            'totale': int(population_totale),
            'source_note': POPULATION_SOURCE_NOTE,
            'par_region': par_region,
            'plus_peuplee': plus_peuplee,
            'plus_dense': plus_dense,
        },
        'superficie_totale_km2': superficie_totale,
        'education': {'universites': Universites.objects.count()},
        'datasets': {'total': sum(par_categorie.values()), 'par_categorie': par_categorie},
        'generated_at': timezone.now().isoformat(),
    }


def region_statistics(pcode):
    region = Region.objects.filter(pcode=pcode).first()
    if region is None:
        return None
    return {
        'pcode': region.pcode,
        'nom': region.nom,
        'population': region.population,
        'superficie_km2': (
            float(region.superficie_km2) if region.superficie_km2 is not None else None
        ),
        'densite': _densite(region.population, region.superficie_km2),
        'nb_departements': region.departements.count(),
        'nb_arrondissements': Arrondissement.objects.filter(
            departement__region=region
        ).count(),
        'nb_communes': Commune.objects.filter(departement__region=region).count(),
        'nb_villages': region.villages.count(),
        'departements': list(
            region.departements.order_by('nom').values('pcode', 'nom', 'population')
        ),
    }
