"""Context processor global : statistiques rapides pour navbar/footer/accueil."""

from django.core.cache import cache

STATS_CACHE_KEY = 'galsenapi_site_stats'
STATS_CACHE_TTL = 60


def _compute_stats():
    from app.models import Universites
    from datasets.models import Dataset
    from geo.models import Arrondissement, Commune, Departement, Region, Village

    return {
        'regions': Region.objects.count(),
        'departements': Departement.objects.count(),
        'arrondissements': Arrondissement.objects.count(),
        'communes': Commune.objects.count(),
        'villages': Village.objects.count(),
        'universites': Universites.objects.count(),
        'datasets': Dataset.objects.filter(is_public=True).count(),
    }


def site_stats(request):
    stats = cache.get(STATS_CACHE_KEY)
    if stats is None:
        try:
            stats = _compute_stats()
        except Exception:
            stats = {}
        else:
            cache.set(STATS_CACHE_KEY, stats, STATS_CACHE_TTL)
    return {'site_stats': stats}
