"""Exporteurs de données brutes par slug de dataset."""
import csv
import json
import io

from django.http import HttpResponse

from app.models import Universites
from agriculture.models import ProductionAgricole
from climat.models import ObservationMensuelle
from economie.models import ObservationEconomique
from geo.models import Arrondissement, Commune, Departement, Region, Village

CONTENT_TYPES = {
    'json': 'application/json',
    'csv': 'text/csv; charset=utf-8',
    'geojson': 'application/geo+json',
}

ADMIN_LEVELS = [
    ('region', Region),
    ('departement', Departement),
    ('arrondissement', Arrondissement),
]


def _parent_pcode(instance, parent_attr):
    parent = getattr(instance, parent_attr, None)
    return parent.pcode if parent else ''


def _admin_rows():
    for niveau, model in ADMIN_LEVELS:
        parent_attr = {'region': None, 'departement': 'region', 'arrondissement': 'departement'}[niveau]
        qs = model.objects.order_by('pcode').select_related(*([parent_attr] if parent_attr else []))
        for instance in qs:
            yield {
                'pcode': instance.pcode,
                'nom': instance.nom,
                'niveau': niveau,
                'parent_pcode': _parent_pcode(instance, parent_attr) if parent_attr else '',
            }


def export_admin_boundaries_json():
    rows = list(_admin_rows())
    return json.dumps(rows, ensure_ascii=False, indent=2), 'json'


def export_admin_boundaries_csv():
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=['pcode', 'nom', 'niveau', 'parent_pcode']
    )
    writer.writeheader()
    writer.writerows(_admin_rows())
    return buffer.getvalue(), 'csv'


def export_admin_boundaries_geojson():
    features = []
    for niveau, model in ADMIN_LEVELS:
        parent_attr = {'region': None, 'departement': 'region', 'arrondissement': 'departement'}[niveau]
        qs = model.objects.order_by('pcode').select_related(*([parent_attr] if parent_attr else []))
        for instance in qs:
            if not instance.geometry:
                continue
            properties = {
                'pcode': instance.pcode,
                'nom': instance.nom,
                'niveau': niveau,
            }
            if parent_attr:
                properties['parent_pcode'] = _parent_pcode(instance, parent_attr)
            if niveau == 'region':
                properties['chef_lieu'] = instance.chef_lieu
            if hasattr(instance, 'population'):
                properties['population'] = instance.population
            if hasattr(instance, 'superficie_km2') and instance.superficie_km2 is not None:
                properties['superficie_km2'] = str(instance.superficie_km2)
            features.append({
                'type': 'Feature',
                'geometry': instance.geometry,
                'properties': properties,
            })
    return json.dumps(
        {'type': 'FeatureCollection', 'features': features},
        ensure_ascii=False,
    ), 'geojson'


def export_villages(fmt):
    rows = [
        {'nom': row['nom'], 'region': row['region__pcode']}
        for row in Village.objects.order_by('region__pcode', 'nom')
        .values('nom', 'region__pcode')
    ]
    return _rows_to_response_payload(rows, ['nom', 'region'], fmt)


def export_communes(fmt):
    rows = [
        {
            'nom': row['nom'],
            'type': row['type'],
            'departement': row['departement__pcode'],
        }
        for row in Commune.objects.order_by('departement__pcode', 'nom')
        .values('nom', 'type', 'departement__pcode')
    ]
    return _rows_to_response_payload(rows, ['nom', 'type', 'departement'], fmt)


def export_population_admin(fmt):
    region_rows = Region.objects.filter(population__isnull=False).order_by('pcode').values(
        'pcode', 'nom', 'population', 'superficie_km2'
    )
    departement_rows = (
        Departement.objects.filter(population__isnull=False)
        .order_by('pcode')
        .select_related('region')
        .values('pcode', 'nom', 'population', 'superficie_km2', 'region__pcode')
    )
    rows = []
    for row in region_rows:
        rows.append({
            'niveau': 'region',
            'pcode': row['pcode'],
            'nom': row['nom'],
            'population': row['population'],
            'superficie_km2': str(row['superficie_km2']) if row['superficie_km2'] is not None else None,
        })
    for row in departement_rows:
        rows.append({
            'niveau': 'departement',
            'pcode': row['pcode'],
            'nom': row['nom'],
            'population': row['population'],
            'superficie_km2': str(row['superficie_km2']) if row['superficie_km2'] is not None else None,
        })
    return _rows_to_response_payload(rows, ['niveau', 'pcode', 'nom', 'population', 'superficie_km2'], fmt)


def export_universites(fmt):
    rows = [{'nom': u.nom, 'logo': u.logo} for u in Universites.objects.order_by('nom')]
    return _rows_to_response_payload(rows, ['nom', 'logo'], fmt)


def export_agriculture_production(fmt):
    rows = [
        {
            'culture_code': row['culture__code_faostat'],
            'culture': row['culture__nom'],
            'element': row['element'],
            'annee': row['annee'],
            'valeur': str(row['valeur']) if row['valeur'] is not None else None,
            'flag': row['flag'],
        }
        for row in ProductionAgricole.objects
        .select_related('culture')
        .order_by('annee', 'culture__code_faostat', 'element')
        .values(
            'culture__code_faostat', 'culture__nom',
            'element', 'annee', 'valeur', 'flag',
        )
    ]
    return _rows_to_response_payload(
        rows, ['culture_code', 'culture', 'element', 'annee', 'valeur', 'flag'], fmt
    )


def export_economie_indicateurs(fmt):
    rows = [
        {
            'code': row['indicateur__code'],
            'nom': row['indicateur__nom'],
            'annee': row['annee'],
            'valeur': str(row['valeur']) if row['valeur'] is not None else None,
            'unite': row['indicateur__unite'],
        }
        for row in ObservationEconomique.objects
        .select_related('indicateur')
        .order_by('indicateur__code', '-annee')
        .values('indicateur__code', 'indicateur__nom', 'indicateur__unite',
                'annee', 'valeur')
    ]
    return _rows_to_response_payload(rows, ['code', 'nom', 'annee', 'valeur', 'unite'], fmt)


def export_climat_observations(fmt):
    rows = [
        {
            'station_id': row['station__station_id'],
            'nom': row['station__nom'],
            'annee': row['annee'],
            'mois': row['mois'],
            'tavg': str(row['tavg']) if row['tavg'] is not None else None,
            'tmin': str(row['tmin']) if row['tmin'] is not None else None,
            'tmax': str(row['tmax']) if row['tmax'] is not None else None,
            'prcp_mm': (
                str(row['prcp_mm']) if row['prcp_mm'] is not None else None
            ),
        }
        for row in ObservationMensuelle.objects
        .select_related('station')
        .order_by('station__station_id', '-annee', '-mois')
        .values(
            'station__station_id', 'station__nom',
            'annee', 'mois', 'tavg', 'tmin', 'tmax', 'prcp_mm',
        )
    ]
    return _rows_to_response_payload(
        rows,
        ['station_id', 'nom', 'annee', 'mois', 'tavg', 'tmin', 'tmax',
         'prcp_mm'],
        fmt,
    )


def _rows_to_response_payload(rows, fieldnames, fmt):
    if fmt == 'json':
        return json.dumps(rows, ensure_ascii=False, indent=2), 'json'
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue(), 'csv'


EXPORTERS = {
    ('sen-admin-boundaries', 'geojson'): export_admin_boundaries_geojson,
    ('sen-admin-boundaries', 'json'): export_admin_boundaries_json,
    ('sen-admin-boundaries', 'csv'): export_admin_boundaries_csv,
    ('sen-population-admin', 'json'): lambda: export_population_admin('json'),
    ('sen-population-admin', 'csv'): lambda: export_population_admin('csv'),
    ('sen-villages', 'json'): lambda: export_villages('json'),
    ('sen-villages', 'csv'): lambda: export_villages('csv'),
    ('sen-communes', 'json'): lambda: export_communes('json'),
    ('sen-communes', 'csv'): lambda: export_communes('csv'),
    ('sen-universites', 'json'): lambda: export_universites('json'),
    ('sen-universites', 'csv'): lambda: export_universites('csv'),
    ('sen-agriculture-production-faostat', 'json'): lambda: export_agriculture_production('json'),
    ('sen-agriculture-production-faostat', 'csv'): lambda: export_agriculture_production('csv'),
    ('sen-economie-indicateurs-banque-mondiale', 'json'): lambda: export_economie_indicateurs('json'),
    ('sen-economie-indicateurs-banque-mondiale', 'csv'): lambda: export_economie_indicateurs('csv'),
    ('sen-climat-observations-noaa', 'json'): lambda: export_climat_observations('json'),
    ('sen-climat-observations-noaa', 'csv'): lambda: export_climat_observations('csv'),
}


def build_download(dataset, fmt):
    key = (dataset.slug, fmt)
    exporter = EXPORTERS.get(key)
    if exporter is None:
        return None
    content, resolved_fmt = exporter()
    body = content.encode('utf-8')
    if resolved_fmt == 'csv':
        body = b'\xef\xbb\xbf' + body
    response = HttpResponse(body, content_type=CONTENT_TYPES[resolved_fmt])
    filename = f'{dataset.slug}.{resolved_fmt}'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
