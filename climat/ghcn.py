"""Pipeline NOAA NCEI GHCN-Daily — stations du Sénégal.

Source : https://www.ncei.noaa.gov/products/land-based-station/
global-historical-climatology-network-daily (domaine public U.S.
Government). Deux accès HTTP :
- inventaire fixed-width : .../pub/data/ghcn/daily/ghcnd-stations.txt
  (ID 1-11, LATITUDE 13-20, LONGITUDE 22-30, ELEVATION 32-37,
  STATE 39-40, NAME 42-71 ; altitude -999.9 = absente) ;
- CSV par station : .../data/global-historical-climatology-network-daily/
  access/{STATION_ID}.csv (valeurs en DIXIÈMES : °C×10 et mm×10 ;
  colonnes *_ATTRIBUTES / flags qualité ignorés).

Le code pays GHCN est le préfixe de 2 caractères de l'ID : le Sénégal
est « SG ». Les IDs SN se répartissent entre SG000… (GSN/legacy) et
SGM000… (réseau mensuel) — le filtre porte donc sur 'SG', pas 'SG000'.

Agrégation mensuelle : tavg/tmin/tmax = moyenne des jours documentés,
prcp_mm = somme, nb_jours = lignes avec au moins une valeur exploitable.
Upsert idempotent en bulk (aucune donnée inventée : mois sans mesure =
NULL).
"""
import csv
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.db import transaction

CACHE_DIR = Path(settings.BASE_DIR) / 'var' / 'ingest' / 'noaa'
STATIONS_URL = (
    'https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt'
)
ACCESS_URL = (
    'https://www.ncei.noaa.gov/data/'
    'global-historical-climatology-network-daily/access/{station_id}.csv'
)
PREFIXE_PAYS_SN = 'SG'
ELEMENTS = ('PRCP', 'TAVG', 'TMAX', 'TMIN')

# Contrôles de réalisme climatique (Sénégal) : plages larges, une valeur
# hors plage est SIGNALÉE dans le rapport sans être modifiée ni supprimée.
# Précipitations annuelles : ~250-350 mm au nord (Podor/Matam) à
# ~1500 mm en Casamance (Ziguinchor/Kédougou) ; Dakar ~300-500 mm.
PLAGE_PRCP_MM_AN = (50, 2500)
# Température moyenne annuelle : ~24-28 °C selon la zone, jamais <20
# ni >35 °C sur une moyenne annuelle complète.
PLAGE_TAVG_ANNUELLE = (20.0, 32.0)

SOURCE_DEFAULTS = {
    'nom': 'NOAA NCEI — GHCN-Daily',
    'url': (
        'https://www.ncei.noaa.gov/products/land-based-station/'
        'global-historical-climatology-network-daily'
    ),
    'publisher': 'National Centers for Environmental Information (NOAA)',
    'license_nom': 'Domaine public (U.S. Government)',
    'license_url': (
        'https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?'
        'id=gov.noaa.ncdc:C00861'
    ),
    'redistribuable': True,
}


def chemin_cache_stations():
    return CACHE_DIR / 'stations.txt'


def chemin_cache_station(station_id):
    return CACHE_DIR / f'{station_id}.csv'


def url_station(station_id):
    return ACCESS_URL.format(station_id=station_id)


def _telecharger(url, dest, timeout=120):
    """GET HTTP avec écriture streaming vers dest (cache local)."""
    requete = urllib.request.Request(
        url, headers={'User-Agent': 'GalsenAPI/1.0 (+django import)'}
    )
    with urllib.request.urlopen(requete, timeout=timeout) as reponse:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, 'wb') as fichier:
            while True:
                bloc = reponse.read(65536)
                if not bloc:
                    break
                fichier.write(bloc)


def telecharger_inventaire(timeout=120):
    """Télécharge ghcnd-stations.txt en cache et retourne son texte."""
    dest = chemin_cache_stations()
    _telecharger(STATIONS_URL, dest, timeout=timeout)
    return dest.read_text(encoding='utf-8')


def lire_inventaire_cache():
    path = chemin_cache_stations()
    if not (path.exists() and path.stat().st_size > 0):
        return None
    return path.read_text(encoding='utf-8')


def telecharger_station_csv(station_id, timeout=120):
    """Télécharge le CSV journalier d'une station en cache."""
    dest = chemin_cache_station(station_id)
    _telecharger(url_station(station_id), dest, timeout=timeout)
    return dest


def lire_station_csv_cache(station_id):
    path = chemin_cache_station(station_id)
    if not (path.exists() and path.stat().st_size > 0):
        return None
    return path


def parse_stations(texte, prefixe_pays=PREFIXE_PAYS_SN):
    """Parse l'inventaire fixed-width -> [{station_id, nom, latitude,
    longitude, altitude}] filtré sur le préfixe pays donné.

    Colonnes officielles (1-based) : ID 1-11, LATITUDE 13-20,
    LONGITUDE 22-30, ELEVATION 32-37, STATE 39-40, NAME 42-71.
    Elevation -999.9 -> altitude=None.
    """
    stations = []
    for ligne in texte.splitlines():
        if not ligne.strip():
            continue
        station_id = ligne[0:11].strip()
        if not station_id.startswith(prefixe_pays):
            continue
        try:
            latitude = Decimal(ligne[12:20].strip())
            longitude = Decimal(ligne[21:30].strip())
        except Exception as erreur:
            raise ValueError(
                f'Ligne inventaire illisible pour {station_id} : {erreur!r}'
            ) from erreur
        brut_altitude = ligne[31:37].strip()
        altitude = None
        if brut_altitude:
            valeur = float(brut_altitude)
            if valeur != -999.9:
                altitude = Decimal(brut_altitude)
        nom = ' '.join(ligne[41:71].split())
        stations.append({
            'station_id': station_id,
            'nom': nom.title(),
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude,
        })
    return stations


def parser_journalier(path):
    """Parse un CSV GHCN access -> liste de lignes journalières.

    Chaque ligne : {'date': date, 'annee': int, 'mois': int,
    'valeurs': {element: Decimal(unités réelles)}} où les dixièmes sont
    déjà convertis (/10). Les éléments hors PRCP/TAVG/TMAX/TMIN et les
    colonnes *_ATTRIBUTES sont ignorés ; valeurs vides ou non numériques
    écartées (jamais interprétées comme 0).
    """
    lignes = []
    with open(path, newline='', encoding='utf-8') as fichier:
        lecteur = csv.DictReader(fichier)
        for brut in lecteur:
            date_brut = (brut.get('DATE') or '').strip()
            if len(date_brut) < 10:
                continue
            valeurs = {}
            for element in ELEMENTS:
                cellule = (brut.get(element) or '').strip()
                if not cellule:
                    continue
                try:
                    valeurs[element] = Decimal(cellule) / 10
                except Exception:
                    continue
            if not valeurs:
                # Ligne sans aucune valeur exploitable : comptée comme
                # jour vide (nb_jours ne la compte pas).
                pass
            lignes.append({
                'date': date_brut,
                'annee': int(date_brut[0:4]),
                'mois': int(date_brut[5:7]),
                'valeurs': valeurs,
            })
    return lignes


def agreer_mensuel(lignes, from_annee=1901):
    """Agrège les lignes journalières par (année, mois).

    Retourne {(annee, mois): {'tavg','tmin','tmax','prcp_mm','nb_jours'}}
    ; moyennes arrondies à 0.01 ; mois présent dans la source mais sans
    valeur mesurée -> champs NULL et nb_jours=0. Les mois totalement
    absents de la source n'apparaissent pas.
    """
    groupes = {}
    for ligne in lignes:
        if ligne['annee'] < from_annee:
            continue
        groupes.setdefault((ligne['annee'], ligne['mois']), []).append(ligne)

    agrege = {}
    for (annee, mois), jours in sorted(groupes.items()):
        cumuls = {}
        for element in ('TAVG', 'TMIN', 'TMAX'):
            presentes = [j['valeurs'][element] for j in jours
                         if element in j['valeurs']]
            cumuls[element] = (
                sum(presentes) / len(presentes) if presentes else None
            )
        precipitations = [j['valeurs']['PRCP'] for j in jours
                          if 'PRCP' in j['valeurs']]
        agrege[(annee, mois)] = {
            'tavg': cumuls['TAVG'],
            'tmin': cumuls['TMIN'],
            'tmax': cumuls['TMAX'],
            'prcp_mm': sum(precipitations) if precipitations else None,
            'nb_jours': sum(1 for j in jours if j['valeurs']),
        }
    return agrege


@transaction.atomic
def importer_station(station_data, agrege_mensuel, source=None):
    """Upsert idempotent StationClimatique + ObservationMensuelle.

    Retourne des stats : créé(s), maj, crees, plages d'années.
    """
    from climat.models import ObservationMensuelle, StationClimatique

    horodatage = datetime.now(timezone.utc).isoformat()
    defaults_station = {
        'nom': station_data['nom'],
        'latitude': station_data['latitude'],
        'longitude': station_data['longitude'],
        'altitude': station_data['altitude'],
        'meta': {
            'source_url': url_station(station_data['station_id']),
            'downloaded_at': horodatage,
        },
    }
    station, created = StationClimatique.objects.update_or_create(
        station_id=station_data['station_id'], defaults=defaults_station,
    )

    existantes = {
        (obs.annee, obs.mois): obs
        for obs in ObservationMensuelle.objects.filter(station=station)
    }
    a_creer, a_maj = [], []
    for (annee, mois), mesures in sorted(agrege_mensuel.items()):
        existante = existantes.pop((annee, mois), None)
        if existante is None:
            a_creer.append(ObservationMensuelle(
                station=station, annee=annee, mois=mois,
                tavg=moyenne_decimal(mesures['tavg']),
                tmin=moyenne_decimal(mesures['tmin']),
                tmax=moyenne_decimal(mesures['tmax']),
                prcp_mm=moyenne_decimal(mesures['prcp_mm']),
                nb_jours=mesures['nb_jours'],
                source=source,
            ))
        else:
            existante.tavg = moyenne_decimal(mesures['tavg'])
            existante.tmin = moyenne_decimal(mesures['tmin'])
            existante.tmax = moyenne_decimal(mesures['tmax'])
            existante.prcp_mm = moyenne_decimal(mesures['prcp_mm'])
            existante.nb_jours = mesures['nb_jours']
            existante.source = source
            a_maj.append(existante)

    ObservationMensuelle.objects.bulk_create(a_creer, batch_size=500)
    if a_maj:
        ObservationMensuelle.objects.bulk_update(
            a_maj,
            ['tavg', 'tmin', 'tmax', 'prcp_mm', 'nb_jours', 'source'],
            batch_size=500,
        )

    annees = sorted({a for (a, _) in agrege_mensuel})
    return station, {
        'station_id': station.station_id,
        'nom': station.nom,
        'cree': created,
        'crees': len(a_creer),
        'maj': len(a_maj),
        'an_min': annees[0] if annees else None,
        'an_max': annees[-1] if annees else None,
        'agrege': agrege_mensuel,
    }


def moyenne_decimal(valeur):
    """Quantize à 2 décimales (None traversant)."""
    if valeur is None:
        return None
    return Decimal(valeur).quantize(Decimal('0.01'))


def controle_realisme(agrege_mensuel):
    """Contrôles de réalisme sur un agrégat mensuel.

    Précipitations annuelles moyennes sur les années quasi-complètes
    (>=300 jours documentés, sinon toutes les années) ; tavg annuel
    moyen sur les mois documentés. Retourne dict de contrôles + liste
    d'anomalies (messages) — aucune donnée n'est modifiée.
    """
    totaux_annuels = {}
    jours_par_annee = {}
    tavg_par_annee = {}
    for (annee, _mois), mesures in agrege_mensuel.items():
        totaux_annuels.setdefault(annee, Decimal('0'))
        if mesures['prcp_mm'] is not None:
            totaux_annuels[annee] += mesures['prcp_mm']
        jours_par_annee.setdefault(annee, 0)
        jours_par_annee[annee] += mesures['nb_jours']
        if mesures['tavg'] is not None:
            tavg_par_annee.setdefault(annee, []).append(mesures['tavg'])

    completes = [a for a, nb in jours_par_annee.items() if nb >= 300]
    base = completes or list(totaux_annuels)
    recentes = sorted(base)[-10:]
    anomalies = []

    prcp_moyen = None
    if recentes:
        prcp_moyen = (
            sum(totaux_annuels[a] for a in recentes) / len(recentes)
        ).quantize(Decimal('0.1'))
        bas, haut = PLAGE_PRCP_MM_AN
        if not (bas <= float(prcp_moyen) <= haut):
            anomalies.append(
                f'précipitations annuelles moyennes {prcp_moyen} mm/an '
                f'hors plage plausible [{bas}; {haut}] mm/an'
            )

    tavg_moyen = None
    tous_tavg = [v for serie in tavg_par_annee.values() for v in serie]
    if tous_tavg:
        tavg_moyen = (
            sum(tous_tavg) / len(tous_tavg)
        ).quantize(Decimal('0.01'))
        bas_t, haut_t = PLAGE_TAVG_ANNUELLE
        if not (bas_t <= float(tavg_moyen) <= haut_t):
            anomalies.append(
                f'température moyenne {tavg_moyen} °C hors plage '
                f'plausible [{bas_t}; {haut_t}] °C'
            )

    return {
        'prcp_moyen_recent': prcp_moyen,
        'tavg_moyen': tavg_moyen,
        'annees_prcp_reference': recentes,
        'anomalies': anomalies,
    }
