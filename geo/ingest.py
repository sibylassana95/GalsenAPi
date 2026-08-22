"""Ingestion HDX COD-AB (limites administratives) + JSON legacy pour l'app geo."""
import json
import zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import requests
from django.conf import settings

from .models import Arrondissement, Commune, Departement, Pays, Region, Village
from .utils import repair_mojibake, slug_nom

DATASET_PAGE_URL = 'https://data.humdata.org/dataset/cod-ab-sen'
GEOJSON_RESOURCE_URL = (
    'https://data.humdata.org/dataset/bd9bc484-155d-41a3-87cf-064310a94492'
    '/resource/02745b5a-88b7-4132-ae11-8bdaf64afff8/download/'
    'sen_admin_boundaries.geojson.zip'
)
LICENSE = 'CC BY-IGO'
SOURCE_NAME = 'HDX COD-AB sen (OCHA ROWCA / ITOS)'
USER_AGENT = 'GalsenAPI/2.0 (+https://github.com/sibylassana95/GalsenAPi)'
REQUEST_TIMEOUT = 60

BASE_DIR = Path(settings.BASE_DIR)
CACHE_DIR = BASE_DIR / 'var' / 'ingest' / 'codab'
EXTRACT_DIR = CACHE_DIR / 'extracted'
REPORTS_DIR = BASE_DIR / 'var' / 'reports'
BACKUP_DIR = BASE_DIR / 'var' / 'backups' / 'dataset'
DATASET_DIR = BASE_DIR / 'dataset'

BBOX_SENEGAL = {'lat_min': 12.3, 'lat_max': 16.7, 'lng_min': -17.6, 'lng_max': -11.3}

NAME_CANDIDATES = {
    1: ['adm1_fr', 'adm1_french', 'adm1_name', 'adm1_en', 'shapeName'],
    2: ['adm2_fr', 'adm2_french', 'adm2_name', 'adm2_en', 'shapeName'],
    3: ['adm3_fr', 'adm3_french', 'adm3_name', 'adm3_en', 'shapeName'],
}
PCODE_CANDIDATES = {
    1: ['adm1_pcode'],
    2: ['adm2_pcode'],
    3: ['adm3_pcode'],
}
EXPECTED_COUNTS = {1: 14, 2: 46, 3: 125}


class ImportReport:
    """Rapport qualité imprimé et persisté sous var/reports/."""

    def __init__(self):
        self.lines = []
        self.counts = {}

    def add(self, line=''):
        self.lines.append(str(line))

    def count(self, key, value):
        self.counts[key] = value
        return value

    def text(self):
        head = [f'Rapport import_geo - {datetime.now().isoformat()}']
        for key, value in self.counts.items():
            head.append(f'{key}: {value}')
        return '\n'.join(head + ['', *self.lines]) + '\n'

    def save(self):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = REPORTS_DIR / f'import_geo_{stamp}.txt'
        path.write_text(self.text(), encoding='utf-8')
        return path


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def download_codab(report=None, offline=False):
    """Télécharge (ou récupère depuis le cache) le zip GeoJSON COD-AB."""
    zip_path = CACHE_DIR / 'sen_admin_boundaries.geojson.zip'
    if zip_path.exists():
        if report:
            report.add(f'Cache utilisé: {zip_path}')
        return zip_path
    if offline:
        raise FileNotFoundError(
            f'--offline: cache absent ({zip_path}). Lance un premier import en ligne.'
        )
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        GEOJSON_RESOURCE_URL,
        timeout=REQUEST_TIMEOUT,
        headers={'User-Agent': USER_AGENT},
        stream=True,
    )
    response.raise_for_status()
    tmp_path = zip_path.with_suffix('.tmp')
    with tmp_path.open('wb') as handle:
        for chunk in response.iter_content(chunk_size=1024 * 512):
            handle.write(chunk)
    tmp_path.replace(zip_path)
    (CACHE_DIR / 'sen_admin_boundaries.geojson.zip.source.txt').write_text(
        f'url={GEOJSON_RESOURCE_URL}\ndataset={DATASET_PAGE_URL}\n'
        f'license={LICENSE}\ndownloaded_at={now_iso()}\n',
        encoding='utf-8',
    )
    if report:
        report.add(f'Téléchargé: {GEOJSON_RESOURCE_URL} -> {zip_path}')
    return zip_path


EXCLUDED_FILE_PATTERNS = ('_em', 'lines', 'points', 'capitals')


def extract_levels(zip_path):
    """Extrait le zip et retourne {niveau_admin: chemin_geojson}.

    Fichiers HDX attendus: sen_admin1.geojson, sen_admin2.geojson, etc.
    Les variantes *_em (cartes vides), lines, points et capitals sont ignorées.
    """
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    levels = {}
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(EXTRACT_DIR)
    for path in sorted(EXTRACT_DIR.rglob('*.geojson')):
        name = path.name.lower()
        if any(pattern in name for pattern in EXCLUDED_FILE_PATTERNS):
            continue
        for level in (0, 1, 2, 3):
            if f'admin{level}' in name or f'adm{level}_' in name:
                levels.setdefault(level, path)
                break
    return levels


def load_features(path):
    data = json.loads(Path(path).read_bytes())
    features = data.get('features', []) if isinstance(data, dict) else data
    return [
        feature for feature in features
        if isinstance(feature, dict) and isinstance(feature.get('geometry'), dict)
    ]


def _lookup(props, names):
    lowered = {key.lower(): value for key, value in props.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value not in (None, ''):
            return value
    return None


def parse_feature(feature, level):
    """Feature GeoJSON -> dict normalisé (pcode, nom, geometry, lat/lng)."""
    props = feature.get('properties') or {}
    pcode = _lookup(props, PCODE_CANDIDATES[level])
    nom = _lookup(props, NAME_CANDIDATES[level])
    geometry = feature['geometry']
    centroid = centroid_from_geometry(geometry)
    return {
        'pcode': str(pcode).strip() if pcode else None,
        'nom': str(nom).strip() if nom else None,
        'geometry': geometry,
        'latitude': Decimal(str(centroid[0])) if centroid else None,
        'longitude': Decimal(str(centroid[1])) if centroid else None,
        'valid_on': _lookup(props, ['validOn', 'valid_on']),
    }


def centroid_from_geometry(geom):
    """Centroïde léger: moyenne des sommets du ring extérieur du plus grand polygone.

    Le « plus grand » est approché par l'aire de la bbox du ring (sans lib géo).
    Retourne (lat, lng) arrondis à 6 décimales ou None.
    """
    if not isinstance(geom, dict):
        return None
    gtype = geom.get('type')
    coords = geom.get('coordinates')
    if gtype == 'Polygon':
        polygons = [coords]
    elif gtype == 'MultiPolygon':
        polygons = coords or []
    else:
        return None
    best_ring, best_area = None, -1.0
    for polygon in polygons:
        if not polygon or not polygon[0]:
            continue
        ring = polygon[0]
        xs = [point[0] for point in ring]
        ys = [point[1] for point in ring]
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        if area > best_area:
            best_area, best_ring = area, ring
    if not best_ring:
        return None
    lat = round(sum(point[1] for point in best_ring) / len(best_ring), 6)
    lng = round(sum(point[0] for point in best_ring) / len(best_ring), 6)
    return lat, lng


def codab_meta(valid_on=None):
    meta = {
        'source': SOURCE_NAME,
        'dataset_url': DATASET_PAGE_URL,
        'resource_url': GEOJSON_RESOURCE_URL,
        'license': LICENSE,
        'date_import': now_iso(),
    }
    if valid_on:
        meta['release_date'] = str(valid_on)
    return meta


def upsert_pays(report):
    senegal_path = DATASET_DIR / 'senegal.json'
    defaults = {'nom': 'Sénégal', 'capitale': 'Dakar', 'monnaie': 'Franc CFA'}
    if senegal_path.exists():
        data = json.loads(senegal_path.read_bytes())
        defaults.update({
            'capitale': repair_mojibake(data.get('capital')) or data.get('capital'),
            'monnaie': repair_mojibake(data.get('monnaie')) or data.get('monnaie'),
            'devise': repair_mojibake(data.get('devise')) or data.get('devise'),
            'indicatif': data.get('indicatif'),
            'population': data.get('habitants'),
            'superficie_km2': data.get('surface'),
        })
    pays, created = Pays.objects.update_or_create(code_iso2='SN', defaults=defaults)
    report.count('pays', 'créé' if created else 'mis à jour')
    return pays


def _region_defaults(pays, item):
    return {
        'pays': pays,
        'nom': item['nom'],
        'geometry': item['geometry'],
        'latitude': item['latitude'],
        'longitude': item['longitude'],
        'meta': codab_meta(item['valid_on']),
    }


def import_codab(features_by_level, report):
    """Upsert hiérarchique Pays -> Régions -> Départements -> Arrondissements.

    features_by_level: {1: [features adm1], 2: [...], 3: [...]}.
    """
    pays = upsert_pays(report)

    created_r = updated_r = skipped_r = 0
    for feature in features_by_level.get(1, []):
        item = parse_feature(feature, 1)
        if not item['pcode'] or not item['nom']:
            skipped_r += 1
            report.add(f"[adm1] ignorée (pcode/nom manquant): {item['nom']}")
            continue
        _, created = Region.objects.update_or_create(
            pcode=item['pcode'], defaults=_region_defaults(pays, item)
        )
        created_r += int(created)
        updated_r += int(not created)

    regions_qs = list(Region.objects.all())
    regions_cache = {r.pcode: r for r in regions_qs}
    regions_slug = {slug_nom(r.nom): r for r in regions_qs}

    created_d = updated_d = skipped_d = 0
    for feature in features_by_level.get(2, []):
        item = parse_feature(feature, 2)
        if not item['pcode'] or not item['nom']:
            skipped_d += 1
            report.add(f"[adm2] ignoré (pcode/nom manquant): {item['nom']}")
            continue
        props = feature.get('properties') or {}
        parent = regions_cache.get(str(_lookup(props, ['adm1_pcode']) or '').strip())
        if parent is None:
            parent_nom = _lookup(props, NAME_CANDIDATES[1]) or ''
            parent = regions_slug.get(slug_nom(parent_nom))
        if parent is None:
            skipped_d += 1
            report.add(f"[adm2] '{item['nom']}' sans région parente, ignoré")
            continue
        _, created = Departement.objects.update_or_create(
            pcode=item['pcode'],
            defaults={
                'region': parent,
                'nom': item['nom'],
                'geometry': item['geometry'],
                'latitude': item['latitude'],
                'longitude': item['longitude'],
                'meta': codab_meta(item['valid_on']),
            },
        )
        created_d += int(created)
        updated_d += int(not created)

    depts_qs = list(Departement.objects.select_related('region'))
    depts_cache = {d.pcode: d for d in depts_qs}
    depts_slug = {(d.region_id, slug_nom(d.nom)): d for d in depts_qs}

    created_a = updated_a = skipped_a = 0
    for feature in features_by_level.get(3, []):
        item = parse_feature(feature, 3)
        if not item['pcode'] or not item['nom']:
            skipped_a += 1
            report.add(f"[adm3] ignoré (pcode/nom manquant): {item['nom']}")
            continue
        props = feature.get('properties') or {}
        parent = depts_cache.get(str(_lookup(props, ['adm2_pcode']) or '').strip())
        if parent is None:
            dept_nom = str(_lookup(props, NAME_CANDIDATES[2]) or '')
            region_nom = str(_lookup(props, NAME_CANDIDATES[1]) or '')
            region = regions_slug.get(slug_nom(region_nom))
            if region is not None:
                parent = depts_slug.get((region.id, slug_nom(dept_nom)))
        if parent is None:
            skipped_a += 1
            report.add(f"[adm3] '{item['nom']}' sans département parent, ignoré")
            continue
        _, created = Arrondissement.objects.update_or_create(
            pcode=item['pcode'],
            defaults={
                'departement': parent,
                'nom': item['nom'],
                'geometry': item['geometry'],
                'latitude': item['latitude'],
                'longitude': item['longitude'],
                'meta': codab_meta(item['valid_on']),
            },
        )
        created_a += int(created)
        updated_a += int(not created)

    counts = {
        'regions_crees': created_r,
        'regions_maj': updated_r,
        'regions_ignores': skipped_r,
        'departements_crees': created_d,
        'departements_maj': updated_d,
        'departements_ignores': skipped_d,
        'arrondissements_crees': created_a,
        'arrondissements_maj': updated_a,
        'arrondissements_ignores': skipped_a,
    }
    for key, value in counts.items():
        report.count(key, value)
    return counts


def _load_legacy(name):
    path = DATASET_DIR / f'{name}.json'
    if not path.exists():
        return []
    return json.loads(path.read_bytes())


def import_legacy(report):
    """Ingestion dataset/commune.json et dataset/village.json (données non géo)."""
    communes_data = _load_legacy('commune')
    villages_data = _load_legacy('village')
    report.count('legacy_communes_lues', len(communes_data))
    report.count('legacy_villages_lus', len(villages_data))

    regions_slug = {slug_nom(r.nom): r for r in Region.objects.all()}
    depts = list(Departement.objects.select_related('region'))
    depts_by_region = {}
    for dept in depts:
        depts_by_region.setdefault(dept.region_id, {})[slug_nom(dept.nom)] = dept
    depts_slug_global = {slug_nom(d.nom): d for d in depts}

    communes_creees = communes_dupliquees = communes_unresolved = 0
    unresolved_communes = []
    seen = set()
    for entry in communes_data:
        nom = repair_mojibake(entry.get('nom', '')) or entry.get('nom', '').strip()
        region_nom = repair_mojibake(entry.get('region', '')) or entry.get('region', '')
        if not nom:
            communes_unresolved += 1
            continue
        region = regions_slug.get(slug_nom(region_nom))
        departement = None
        if region is not None and region.id in depts_by_region:
            departement = depts_by_region[region.id].get(slug_nom(nom))
        if departement is None:
            candidat = depts_slug_global.get(slug_nom(nom))
            if candidat is not None:
                departement = candidat
                region = candidat.region
        if departement is None:
            communes_unresolved += 1
            unresolved_communes.append(f"{nom} ({region_nom})")
            continue
        key = (departement.id, slug_nom(nom))
        if key in seen:
            communes_dupliquees += 1
            continue
        _, created = Commune.objects.get_or_create(
            departement=departement,
            nom=nom,
            defaults={
                'meta': {
                    'source': 'dataset/commune.json (GalsenAPI legacy)',
                    'region_declaree': region_nom,
                    'date_import': now_iso(),
                }
            },
        )
        seen.add(key)
        if created:
            communes_creees += 1
        else:
            communes_dupliquees += 1

    villages_crees = villages_dupliques = villages_unresolved = 0
    unresolved_villages = []
    seen_villages = set()
    for entry in villages_data:
        nom_brut = repair_mojibake(entry.get('nom', '')) or entry.get('nom', '')
        region_nom = repair_mojibake(entry.get('region', '')) or entry.get('region', '')
        nom = nom_brut.strip()
        region = regions_slug.get(slug_nom(region_nom))
        if not nom or region is None:
            villages_unresolved += 1
            unresolved_villages.append(f"{nom_brut} ({region_nom})")
            continue
        suffixe = f", {region.nom}"
        if nom.lower().endswith(suffixe.lower()):
            nom = nom[: -len(suffixe)].strip()
        key = (region.id, slug_nom(nom))
        if key in seen_villages:
            villages_dupliques += 1
            continue
        _, created = Village.objects.get_or_create(
            region=region,
            nom=nom,
            defaults={
                'meta': {
                    'source': 'dataset/village.json (GalsenAPI legacy)',
                    'date_import': now_iso(),
                }
            },
        )
        seen_villages.add(key)
        if created:
            villages_crees += 1
        else:
            villages_dupliques += 1

    report.count('communes_creees', communes_creees)
    report.count('communes_doublons', communes_dupliquees)
    report.count('communes_non_resolues', communes_unresolved)
    report.count('villages_crees', villages_crees)
    report.count('villages_doublons', villages_dupliques)
    report.count('villages_non_resolus', villages_unresolved)
    if unresolved_communes:
        report.add(f"Communes non résolues ({len(unresolved_communes)}): "
                   + ', '.join(unresolved_communes[:30])
                   + (' ...' if len(unresolved_communes) > 30 else ''))
    if unresolved_villages:
        report.add(f"Villages non résolus ({len(unresolved_villages)}): "
                   + ', '.join(unresolved_villages[:30])
                   + (' ...' if len(unresolved_villages) > 30 else ''))
    return {
        'communes_creees': communes_creees,
        'villages_crees': villages_crees,
    }


def validate(report):
    """Contrôles qualité: comptages attendus, bbox Sénégal, géométries."""
    attendu = {'regions': EXPECTED_COUNTS[1], 'departements': EXPECTED_COUNTS[2],
               'arrondissements': EXPECTED_COUNTS[3]}
    obtenus = {
        'regions': Region.objects.count(),
        'departements': Departement.objects.count(),
        'arrondissements': Arrondissement.objects.count(),
        'communes': Commune.objects.count(),
        'villages': Village.objects.count(),
    }
    report.add('')
    report.add('=== Validation ===')
    for key, valeur in attendu.items():
        obtenu = obtenus[key]
        ecart_ok = (
            obtenu == valeur if key != 'arrondissements'
            else 120 <= obtenu <= 130
        )
        statut = 'OK' if ecart_ok else 'ÉCART'
        report.add(f"{key}: attendu={valeur} obtenu={obtenu} [{statut}]")
    for key in ('communes', 'villages'):
        report.add(f"{key}: obtenu={obtenus[key]}")

    sans_geo = {
        'regions': Region.objects.filter(geometry__isnull=True).count(),
        'departements': Departement.objects.filter(geometry__isnull=True).count(),
        'arrondissements': Arrondissement.objects.filter(geometry__isnull=True).count(),
    }
    report.add(f"géométries manquantes: {sans_geo}")
    report.count('geometries_manquantes', sum(sans_geo.values()))

    hors_bbox = []
    for model, label in ((Region, 'région'), (Departement, 'dépt'),
                         (Arrondissement, 'arrondt')):
        for obj in model.objects.exclude(latitude=None, longitude=None):
            lat, lng = float(obj.latitude), float(obj.longitude)
            if not (BBOX_SENEGAL['lat_min'] <= lat <= BBOX_SENEGAL['lat_max']
                    and BBOX_SENEGAL['lng_min'] <= lng <= BBOX_SENEGAL['lng_max']):
                hors_bbox.append(f'{label} {obj.nom}: ({lat}, {lng})')
    report.count('coordonnees_hors_bbox', len(hors_bbox))
    if hors_bbox:
        report.add(f"Coordonnées hors bbox Sénégal ({len(hors_bbox)}): "
                   + '; '.join(hors_bbox[:20]))
    dakar = Region.objects.filter(nom__iexact='Dakar').first()
    if dakar and dakar.latitude is not None:
        report.add(
            f"Dakar: lat={dakar.latitude} lng={dakar.longitude} "
            f"(attendu ~14.7 / ~-17.4)"
        )
    report.add('')
    report.add(f"Totaux: {obtenus}")
    return obtenus

