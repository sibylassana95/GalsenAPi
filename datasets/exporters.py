"""Exporteurs de données brutes par slug de dataset."""
import csv
import json
import io

from django.http import HttpResponse

from app.models import Universites
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
