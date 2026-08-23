"""Catalogue des sources et datasets référencés (données factuelles uniquement)."""


def _record_counts():
    from app.models import Universites
    from datasets.models import DataSource
    from geo.models import Arrondissement, Commune, Departement, Region, Village

    return {
        'sen-admin-boundaries': (
            Region.objects.count()
            + Departement.objects.count()
            + Arrondissement.objects.count()
        ),
        'sen-population-admin': (
            Region.objects.filter(population__isnull=False).count()
            + Departement.objects.filter(population__isnull=False).count()
        ),
        'sen-villages': Village.objects.count(),
        'sen-communes': Commune.objects.count(),
        'sen-universites': Universites.objects.count(),
    }


def _missing_coords():
    from geo.models import Arrondissement, Departement, Region

    return (
        Region.objects.filter(geometry__isnull=True).count()
        + Departement.objects.filter(geometry__isnull=True).count()
        + Arrondissement.objects.filter(geometry__isnull=True).count()
    )


def _fmt_nombre(n):
    return f'{n:,}'.replace(',', ' ')


CATALOG = [
    {
        'source': {
            'nom': 'HDX / OCHA COD-AB',
            'slug': 'hdx-cod-ab',
            'url': 'https://data.humdata.org/dataset/cod-ab-sen',
            'publisher': "Centre de données humanitaires communes (OCHA)",
            'license_nom': 'CC BY-IGO',
            'license_url': 'https://data.humdata.org/faqs/terms',
            'redistribuable': True,
        },
        'datasets': [
            {
                'slug': 'sen-admin-boundaries',
                'titre': 'Limites administratives du Sénégal',
                'description': (
                    'Frontières géoréférencées des 14 régions, 46 départements '
                    'et 125 arrondissements avec P-codes officiels.'
                ),
                'categorie': 'geographie',
                'coverage_period': '2024-2026',
                'update_frequency': 'irrégulière',
                'export_formats': ['geojson', 'json', 'csv'],
                'methodology': (
                    'Import GeoJSON HDX COD-AB (sen_admin_boundaries.geojson.zip) '
                    'via manage.py import_geo ; centroïdes calculés.'
                ),
            },
            {
                'slug': 'sen-population-admin',
                'titre': 'Population par région et département',
                'description': (
                    "Chiffres de population par région et département issus du jeu "
                    "de données historique Galsenify (base ANSD). À remplacer par "
                    "le RGPH-5 2023."
                ),
                'categorie': 'demographie',
                'coverage_period': '≈2023',
                'update_frequency': 'censaire',
                'export_formats': ['json', 'csv'],
                'methodology': (
                    'Enrichissement des entités administratives depuis les JSON '
                    'legacy Galsenify (meta.population_source).'
                ),
            },
        ],
    },
    {
        'source': {
            'nom': 'Galsenify (Daouda BA)',
            'slug': 'galsenify',
            'url': 'https://github.com/GalsenDev221/galsenify',
            'publisher': 'GalsenDev221',
            'license_nom': 'MIT',
            'license_url': 'https://github.com/GalsenDev221/galsenify/blob/master/LICENSE',
            'redistribuable': True,
        },
        'datasets': [
            {
                'slug': 'sen-villages',
                'titre': 'Villages du Sénégal',
                'description': lambda counts: (
                    'Liste historique des villages par région '
                    f'({_fmt_nombre(counts.get("sen-villages", 0))} après déduplication).'
                ),
                'categorie': 'geographie',
                'export_formats': ['json', 'csv'],
            },
            {
                'slug': 'sen-communes',
                'titre': 'Communes du Sénégal',
                'description': lambda counts: (
                    'Communes rattachées aux départements quand le rattachement a '
                    f'pu être établi ({counts.get("sen-communes", 0)}/618 résolues '
                    '— enrichissement en cours).'
                ),
                'categorie': 'geographie',
                'export_formats': ['json', 'csv'],
            },
            {
                'slug': 'sen-universites',
                'titre': 'Universités et écoles de formation',
                'description': lambda counts: (
                    "Liste des établissements d'enseignement supérieur et de "
                    f'formation ({counts.get("sen-universites", 0)}) avec logos.'
                ),
                'categorie': 'education',
                'export_formats': ['json', 'csv'],
            },
        ],
    },
]
