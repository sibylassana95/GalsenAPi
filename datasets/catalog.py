"""Catalogue des sources et datasets référencés (données factuelles uniquement)."""


def _record_counts():
    from agriculture.models import ProductionAgricole
    from app.models import Universites
    from datasets.models import DataSource
    from demographie.models import PopulationRecord
    from economie.models import ObservationEconomique
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
        'sen-population-rgph5-2023': PopulationRecord.objects.count(),
        'sen-villages': Village.objects.count(),
        'sen-communes': Commune.objects.count(),
        'sen-universites': Universites.objects.count(),
        'sen-agriculture-production-faostat': ProductionAgricole.objects.count(),
        'sen-economie-indicateurs-banque-mondiale': (
            ObservationEconomique.objects.count()
        ),
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
                'titre': 'Population par région et département (legacy)',
                'description': (
                    "Chiffres de population hérités du jeu de données historique "
                    "Galsenify (base ANSD), désormais supplantés par le RGPH-5 2023 "
                    "(voir le dataset sen-population-rgph5-2023). Conservés à titre "
                    "de référence historique."
                ),
                'categorie': 'demographie',
                'coverage_period': '≈2023 (hérité)',
                'update_frequency': 'censaire',
                'export_formats': ['json', 'csv'],
                'methodology': (
                    'Enrichissement des entités administratives depuis les JSON '
                    'legacy Galsenify (meta.population_source) ; valeurs écrasées '
                    'par manage.py import_demographie après import du RGPH-5.'
                ),
            },
        ],
    },
    {
        'source': {
            'nom': 'ANSD',
            'slug': 'ansd',
            'url': 'https://www.ansd.sn',
            'publisher': 'Agence Nationale de la Statistique et de la Démographie',
            'license_nom': 'CC BY 4.0',
            'license_url': 'https://anads.ansd.sn',
            'redistribuable': True,
        },
        'datasets': [
            {
                'slug': 'sen-population-rgph5-2023',
                'titre': 'Population RGPH-5 2023',
                'description': (
                    "Population résidente par région (14) et par département (46) "
                    "selon le 5e Recensement Général de la Population et de "
                    "l'Habitat (RGPH-5, ANSD, résultats définitifs). Total "
                    f'national : {_fmt_nombre(18126390)} habitants.'
                ),
                'categorie': 'demographie',
                'coverage_period': '2023',
                'update_frequency': 'censaire',
                'export_formats': ['json', 'csv'],
                'methodology': (
                    'Import depuis data/rgph5_2023.json extrait du rapport '
                    'définitif RGPH-5 Thème I (tableaux I-9 et I-21) via '
                    'manage.py import_demographie ; rafraîchit geo.Region / '
                    'geo.Departement.population.'
                ),
            },
        ],
    },
    {
        'source': {
            'nom': 'FAO — FAOSTAT',
            'slug': 'faostat',
            'url': 'https://www.fao.org/faostat/en/#data/QCL',
            'publisher': "Organisation des Nations unies pour l'alimentation "
                         "et l'agriculture",
            'license_nom': 'CC BY 4.0',
            'license_url': 'https://www.fao.org/contact-us/terms/db-terms-of-use/en',
            'redistribuable': True,
        },
        'datasets': [
            {
                'slug': 'sen-agriculture-production-faostat',
                'titre': 'Production agricole FAOSTAT (Sénégal)',
                'description': (
                    "Production (tonnes), superficie récoltée (ha) et rendement "
                    "(hg/ha) par culture et produit agricole au Sénégal, de 1961 "
                    "à la dernière année publiée, d'après le dataset QCL "
                    "(Production, Crops and livestock products) de FAOSTAT. Les "
                    "rendements sources en kg/ha sont convertis en hg/ha "
                    "(x10, valeur source conservée dans meta.unite_source)."
                ),
                'categorie': 'agriculture',
                'coverage_period': '1961-2024',
                'update_frequency': 'annuelle',
                'export_formats': ['json', 'csv'],
                'methodology': (
                    'Bulk FAOSTAT QCL normalisé filtré Sénégal via '
                    'manage.py import_agriculture'
                ),
            },
        ],
    },
    {
        'source': {
            'nom': 'Banque mondiale',
            'slug': 'worldbank',
            'url': 'https://data.worldbank.org',
            'publisher': 'World Bank Group',
            'license_nom': 'CC BY 4.0',
            'license_url': (
                'https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets'
            ),
            'redistribuable': True,
        },
        'datasets': [
            {
                'slug': 'sen-economie-indicateurs-banque-mondiale',
                'titre': 'Indicateurs économiques du Sénégal (Banque mondiale)',
                'description': lambda counts: (
                    "Série annuelle d'indicateurs macroéconomiques du "
                    'Sénégal (PIB et croissance, inflation, emploi, commerce '
                    'extérieur, dette et finance publique, structure '
                    'sectorielle, accès à l\u2019électricité) issus de '
                    "l'API World Bank Indicators : "
                    f'{counts.get("sen-economie-indicateurs-banque-mondiale", 0)} '
                    'observations pour ~21 indicateurs, de 1960 à la dernière '
                    'année publiée.'
                ),
                'categorie': 'economie',
                'coverage_period': '1960-2025',
                'update_frequency': 'annuelle',
                'export_formats': ['json', 'csv'],
                'methodology': (
                    "Import sélectif de l'API api.worldbank.org (format json, "
                    'date=1960:2026) filtrée sur le Sénégal via '
                    'manage.py import_economie ; les années sans valeur '
                    "(value=null) sont écartées ; noms officiels EN conservés "
                    '(nom_officiel) à côté des libellés FR courts.'
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
