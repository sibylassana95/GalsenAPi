"""Pipeline World Bank Indicators — Sénégal.

Source : API officielle https://api.worldbank.org/v2/country/SEN/indicator/
<code>?format=json&per_page=25000&date=1960:2026, licence CC BY 4.0.
Structure de réponse : [meta_page, [observations...]] ; les années sans
donnée portent value=None et sont écartées à l'import (comptées comme
'sans donnee' dans le rapport).
"""
import json
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.db import transaction

CACHE_DIR = Path(settings.BASE_DIR) / 'var' / 'ingest' / 'worldbank'
DATE_MIN = 1960
DATE_MAX = 2026

# Contrôle réaliste du dernier point NY.GDP.MKTP.CD (US$ courants) :
# le PIB sénégalais récent est ~3e10 US$ (2024 ≈ 32 Md). Hors de cette
# fourchette large -> incohérence signalée dans le rapport.
PLAGE_PIB_USD = (10_000_000_000, 500_000_000_000)


def chemin_cache(code):
    return CACHE_DIR / f'{code}.json'


def telecharger(code, timeout=60):
    """GET l'indicateur depuis l'API et écrit le JSON brut en cache.

    Retourne le payload décodé [[meta], [data...]].
    """
    from economie.indicators import url_indicateur

    url = url_indicateur(code)
    requete = urllib.request.Request(
        url, headers={'User-Agent': 'GalsenAPI/1.0 (+django import)'}
    )
    # URL constante https du projet (pas de scheme arbitraire)  # nosec B310
    with urllib.request.urlopen(requete, timeout=timeout) as reponse:  # nosec B310
        brut = reponse.read()
    payload = json.loads(brut)
    dest = chemin_cache(code)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(brut)
    return payload


def lire_cache(code):
    """Charge le JSON en cache pour un code (None si absent)."""
    path = chemin_cache(code)
    if not (path.exists() and path.stat().st_size > 0):
        return None
    return json.loads(path.read_bytes())


def parse_reponse(payload):
    """Parse une réponse WB -> dict {annee: Decimal} (les null sont écartés).

    Retourne aussi la méta : nom_officiel (indicator.value), total_lignes,
    lastupdated.
    """
    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        raise ValueError('Réponse World Bank inattendue (pas [[meta],[data]]).')
    meta_page = payload[0] or {}
    lignes = payload[1]
    valeurs = {}
    decimal_wb = ''
    nom_officiel = ''
    for ligne in lignes:
        nom_officiel = nom_officiel or str(
            (ligne.get('indicator') or {}).get('value') or ''
        )
        brut = ligne.get('value')
        if brut is None:
            continue
        try:
            valeur = Decimal(str(brut))
        except InvalidOperation:
            continue
        annee = int(ligne['date'])
        valeurs[annee] = valeur
        if not decimal_wb:
            decimal_wb = str(ligne.get('decimal', ''))
    return {
        'valeurs': valeurs,
        'nom_officiel': nom_officiel,
        'decimal': decimal_wb,
        'total_lignes': int(meta_page.get('total', len(lignes))),
        'lastupdated': str(meta_page.get('lastupdated', '')),
    }


@transaction.atomic
def importer_indicateur(code, parse_result, source=None, api_url=''):
    """Upsert idempotent IndicateurEconomique + ObservationEconomique.

    parse_result vient de parse_reponse(). Retourne des stats par indicateur.
    """
    from economie.indicators import INDICATEURS_PAR_CODE
    from economie.models import IndicateurEconomique, ObservationEconomique

    definition = INDICATEURS_PAR_CODE.get(code)
    if definition is None:
        raise ValueError(f'Code {code} hors curateur economie/indicators.py')
    nom_fr, categorie, unite = definition

    horodatage = datetime.now(timezone.utc).isoformat()
    indicateur, created = IndicateurEconomique.objects.update_or_create(
        code=code,
        defaults={
            'nom': nom_fr,
            'nom_officiel': parse_result['nom_officiel'],
            'categorie': categorie,
            'unite': unite,
            'decimal': parse_result.get('decimal', ''),
            'source': source,
            'meta': {'api_url': api_url, 'downloaded_at': horodatage},
        },
    )

    valeurs = parse_result['valeurs']
    existants = {
        obs.annee: obs
        for obs in ObservationEconomique.objects.filter(indicateur=indicateur)
    }
    a_creer, a_maj = [], []
    for annee, valeur in sorted(valeurs.items()):
        obs = existants.pop(annee, None)
        if obs is None:
            a_creer.append(ObservationEconomique(
                indicateur=indicateur, annee=annee, valeur=valeur,
            ))
        else:
            obs.valeur = valeur
            a_maj.append(obs)
    # Années devenues vides côté source ? On ne supprime pas : les nulls ne
    # créent jamais d'observation, et les observations existantes restent
    # historiques (pas de destructive delete).

    ObservationEconomique.objects.bulk_create(a_creer, batch_size=500)
    if a_maj:
        ObservationEconomique.objects.bulk_update(
            a_maj, ['valeur'], batch_size=500
        )

    plage = sorted(valeurs)
    derniere_annee = plage[-1] if plage else None
    stats = {
        'code': code,
        'nom': nom_fr,
        'cree': created,
        'observations': len(a_creer) + len(a_maj),
        'crees': len(a_creer),
        'maj': len(a_maj),
        'sans_donnee': parse_result['total_lignes'] - len(valeurs),
        'an_min': plage[0] if plage else None,
        'an_max': derniere_annee,
        'derniere_valeur': valeurs.get(derniere_annee),
    }
    return indicateur, stats
