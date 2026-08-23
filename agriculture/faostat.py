"""Pipeline FAOSTAT QCL (Production, Crops and livestock products) — Sénégal.

Source : bulk officiel « Normalized » (format long), licence CC BY 4.0.
Découvertes sur le fichier réel (2026) :
- Yield est publié en kg/ha (et plus en hg/ha) -> conversion x10 documentée
  dans ProductionAgricole.meta pour conserver la valeur source exacte ;
- Production existe en 't' et '1000 No' ; seul 't' est retenu (unité cohérente
  avec production_tonnes) ;
- Area harvested est publié en ha.
"""
import csv
import io
import urllib.request
import zipfile
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.db import transaction

BULK_URL = (
    'https://bulks-faostat.fao.org/production/'
    'Production_Crops_Livestock_E_All_Data_(Normalized).zip'
)
ZIP_NAME = 'Production_Crops_Livestock_E_All_Data_(Normalized).zip'
CACHE_DIR = Path(settings.BASE_DIR) / 'var' / 'ingest' / 'faostat'
CSV_MEMBER_PATTERN = 'Production_Crops_Livestock_E_All_Data'
AREA_NAME = 'Senegal'

# Élément FAOSTAT (minuscule) -> (code interne, unités acceptées).
ELEMENT_MAPPING = {
    'area harvested': ('superficie_recoltee_ha', {'ha'}),
    'yield': ('rendement_hg_ha', {'kg/ha'}),
    'production': ('production_tonnes', {'t'}),
}
KG_HA_TO_HG_HA = Decimal('10')

SOURCE_DEFAULTS = {
    'nom': 'FAO — FAOSTAT',
    'url': 'https://www.fao.org/faostat/en/#data/QCL',
    'publisher': "Organisation des Nations unies pour l'alimentation "
                 "et l'agriculture",
    'license_nom': 'CC BY 4.0',
    'license_url': 'https://www.fao.org/contact-us/terms/db-terms-of-use/en',
    'redistribuable': True,
}


def chemin_cache():
    return CACHE_DIR / ZIP_NAME


def telecharger_bulk(timeout=300):
    """Télécharge le bulk FAOSTAT dans le cache local si absent.

    Retourne le chemin du zip en cache.
    """
    dest = chemin_cache()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    tmp = dest.with_name(dest.name + '.part')
    requete = urllib.request.Request(
        BULK_URL, headers={'User-Agent': 'GalsenAPI/1.0 (+django import)'}
    )
    # URL constante https du projet (pas de scheme arbitraire)  # nosec B310
    with urllib.request.urlopen(requete, timeout=timeout) as reponse:  # nosec B310
        with open(tmp, 'wb') as fichier:
            while True:
                bloc = reponse.read(1 << 20)
                if not bloc:
                    break
                fichier.write(bloc)
    tmp.replace(dest)
    return dest


def membre_donnees(zip_path):
    """Nom du membre CSV de données dans le zip (le plus gros CSV de données)."""
    with zipfile.ZipFile(zip_path) as archive:
        candidats = [
            info for info in archive.infolist()
            if info.filename.lower().endswith('.csv')
            and CSV_MEMBER_PATTERN in info.filename
        ]
        if not candidats:
            raise FileNotFoundError(
                f'Aucun CSV "{CSV_MEMBER_PATTERN}*" dans {Path(zip_path).name}'
            )
        return max(candidats, key=lambda i: i.file_size).filename


def lignes_normalisees(flux_binaire):
    """Parse en streaming un flux binaire CSV FAOSTAT normalisé.

    Yields des dicts : item_code, item_nom, element, unit, annee, valeur, flag.
    Ne filtre PAS encore la zone (le filtrage Sénégal se fait au niveau appelant).
    """
    wrapper = io.TextIOWrapper(flux_binaire, encoding='latin-1')
    reader = csv.DictReader(wrapper)
    colonnes = {(c or '').strip().lower(): c for c in (reader.fieldnames or [])}
    requis = ['area', 'item code', 'item', 'element', 'year', 'unit', 'value', 'flag']
    manquantes = [c for c in requis if c not in colonnes]
    if manquantes:
        raise ValueError(f'Colonnes FAOSTAT manquantes : {manquantes}')
    for ligne in reader:
        yield {
            'area': (ligne[colonnes['area']] or '').strip(),
            'item_code': (ligne[colonnes['item code']] or '').strip(),
            'item_nom': (ligne[colonnes['item']] or '').strip(),
            'element': (ligne[colonnes['element']] or '').strip(),
            'unit': (ligne[colonnes['unit']] or '').strip(),
            'annee': (ligne[colonnes['year']] or '').strip(),
            'valeur': (ligne[colonnes['value']] or '').strip(),
            'flag': (ligne[colonnes['flag']] or '').strip(),
        }


def _decimal(valeur_brute):
    """Decimal ou None (vide / non numérique comme 'No numeric')."""
    if not valeur_brute:
        return None
    try:
        return Decimal(valeur_brute)
    except InvalidOperation:
        return None


@transaction.atomic
def importer_lignes(lignes_senegal, source=None, years_from=1961, meta_base=None):
    """Upsert idempotent Culture + ProductionAgricole depuis des lignes Sénégal.

    Retourne un dict de statistiques.
    """
    meta_base = dict(meta_base or {})
    cultures_creees = 0
    compteurs = Counter()
    ignores_elements = Counter()
    an_min = an_max = None
    records = {}
    noms_cultures = {}

    for ligne in lignes_senegal:
        clef_element = ligne['element'].lower()
        mapping = ELEMENT_MAPPING.get(clef_element)
        if mapping is None:
            ignores_elements[ligne['element']] += 1
            continue
        element_code, unites = mapping
        if ligne['unit'] not in unites:
            ignores_elements[f'{ligne["element"]} ({ligne["unit"]})'] += 1
            continue
        try:
            annee = int(ligne['annee'])
        except (TypeError, ValueError):
            continue
        if annee < years_from:
            continue
        code = ligne['item_code']
        if not code:
            continue
        noms_cultures[code] = ligne['item_nom']

        valeur = _decimal(ligne['valeur'])
        record_meta = dict(meta_base)
        if element_code == 'rendement_hg_ha' and valeur is not None:
            valeur = valeur * KG_HA_TO_HG_HA
            record_meta['unite_source'] = 'kg/ha'
            record_meta['conversion'] = 'x10 vers hg/ha'
        records[(code, annee, element_code)] = {
            'valeur': valeur,
            'flag': ligne['flag'][:3],
            'meta': record_meta,
        }
        compteurs[element_code] += 1
        an_min = annee if an_min is None else min(an_min, annee)
        an_max = annee if an_max is None else max(an_max, annee)

    from agriculture.models import Culture, ProductionAgricole

    existants_cultures = {
        c.code_faostat: c for c in Culture.objects.all()
    }
    objets_cultures = {}
    for code, nom in sorted(noms_cultures.items()):
        culture, created = Culture.objects.update_or_create(
            code_faostat=code, defaults={'nom': nom}
        )
        objets_cultures[code] = culture
        existants_cultures.pop(code, None)
        if created:
            cultures_creees += 1

    culture_ids = {c.id for c in objets_cultures.values()}
    existants = {}
    qs = ProductionAgricole.objects.filter(culture_id__in=culture_ids)
    for prod in qs:
        existants[(prod.culture.code_faostat, prod.annee, prod.element)] = prod

    a_creer, a_maj = [], []
    for (code, annee, element_code), payload in records.items():
        prod = existants.get((code, annee, element_code))
        if prod is None:
            a_creer.append(ProductionAgricole(
                culture=objets_cultures[code], annee=annee,
                element=element_code, source=source, **payload,
            ))
        else:
            prod.valeur = payload['valeur']
            prod.flag = payload['flag']
            prod.meta = payload['meta']
            prod.source = source
            a_maj.append(prod)

    ProductionAgricole.objects.bulk_create(a_creer, batch_size=500)
    if a_maj:
        ProductionAgricole.objects.bulk_update(
            a_maj, ['valeur', 'flag', 'meta', 'source'], batch_size=500
        )

    return {
        'cultures_total': len(noms_cultures),
        'cultures_creees': cultures_creees,
        'crees': len(a_creer),
        'maj': len(a_maj),
        'compteurs': dict(compteurs),
        'ignores_elements': dict(ignores_elements),
        'an_min': an_min,
        'an_max': an_max,
        'horodatage': datetime.now(timezone.utc).isoformat(),
    }
