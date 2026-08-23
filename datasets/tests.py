import json

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase

from datasets.exporters import build_download
from datasets.models import DataSource, Dataset, DatasetVersion
from geo.models import Departement, Pays, Region, Village


def build_geo_data():
    pays = Pays.objects.create(nom='Sénégal', code_iso2='SN')
    region = Region.objects.create(
        pays=pays, pcode='SN01', nom='Dakar', population=3100000,
        superficie_km2='1831.00',
        geometry={'type': 'Polygon', 'coordinates': [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    )
    Departement.objects.create(
        region=region, pcode='SN011', nom='Dakar', population=100000,
        geometry={'type': 'Polygon', 'coordinates': [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    )
    Village.objects.create(region=region, nom='Ngor', population=5000)
    Village.objects.create(region=region, nom='Yoff', population=12000)
    return region


class ModelTests(TestCase):
    def test_str_et_ordering(self):
        source = DataSource.objects.create(
            nom='HDX / OCHA COD-AB', slug='hdx-cod-ab',
            url='https://data.humdata.org/dataset/cod-ab-sen',
            license_nom='CC BY-IGO',
        )
        dataset = Dataset.objects.create(
            titre='Limites administratives du Sénégal', slug='sen-admin-boundaries',
            description='Frontières.', categorie='geographie', source=source,
        )
        self.assertEqual(str(source), 'HDX / OCHA COD-AB')
        self.assertEqual(str(dataset), 'Limites administratives du Sénégal')
        version = DatasetVersion.objects.create(dataset=dataset)
        self.assertEqual(str(version), 'sen-admin-boundaries v1.0.0')

    def test_slugs_uniques(self):
        DataSource.objects.create(nom='A', slug='src-a', url='https://a.example', license_nom='MIT')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DataSource.objects.create(nom='B', slug='src-a', url='https://b.example', license_nom='MIT')
        source = DataSource.objects.get(slug='src-a')
        Dataset.objects.create(titre='T1', slug='ds-x', description='D', categorie='autre', source=source)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Dataset.objects.create(titre='T2', slug='ds-x', description='D', categorie='autre', source=source)

    def test_version_unique_together(self):
        source = DataSource.objects.create(nom='S', slug='s', url='https://s.example', license_nom='MIT')
        dataset = Dataset.objects.create(
            titre='T', slug='t', description='D', categorie='autre', source=source,
        )
        DatasetVersion.objects.create(dataset=dataset, version_number='1.0.0')
        with self.assertRaises(IntegrityError):
            DatasetVersion.objects.create(dataset=dataset, version_number='1.0.0')


class SyncDatasetsTests(TestCase):
    def setUp(self):
        build_geo_data()

    def test_sync_idempotent(self):
        call_command('sync_datasets', verbosity=0)
        first_datasets = Dataset.objects.count()
        first_sources = DataSource.objects.count()
        first_versions = list(DatasetVersion.objects.values_list('dataset__slug', 'version_number'))
        first_counts = {
            slug: DatasetVersion.objects.get(dataset__slug=slug, version_number='1.0.0').record_count
            for slug in Dataset.objects.values_list('slug', flat=True)
        }

        call_command('sync_datasets', verbosity=0)

        self.assertEqual(Dataset.objects.count(), first_datasets)
        self.assertEqual(DataSource.objects.count(), first_sources)
        second_versions = list(DatasetVersion.objects.values_list('dataset__slug', 'version_number'))
        self.assertEqual(first_versions, second_versions)
        second_counts = {
            slug: DatasetVersion.objects.get(dataset__slug=slug, version_number='1.0.0').record_count
            for slug in Dataset.objects.values_list('slug', flat=True)
        }
        self.assertEqual(first_counts, second_counts)

    def test_record_counts_calculs(self):
        call_command('sync_datasets', verbosity=0)
        admin = Dataset.objects.get(slug='sen-admin-boundaries').versions.first()
        self.assertEqual(
            admin.record_count,
            Region.objects.count() + Departement.objects.count(),
        )
        villages = Dataset.objects.get(slug='sen-villages').versions.first()
        self.assertGreater(villages.record_count, 0)


class DatasetsApiTests(TestCase):
    def setUp(self):
        build_geo_data()
        call_command('sync_datasets', verbosity=0)

    def api_get(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)
        return response.json()

    def test_list_contient_sen_villages(self):
        data = self.api_get('/api/v1/datasets/')
        slugs = [row['slug'] for row in data['results']]
        self.assertIn('sen-villages', slugs)
        row = next(r for r in data['results'] if r['slug'] == 'sen-villages')
        self.assertGreater(row['latest_version']['record_count'], 0)
        self.assertEqual(row['categorie_label'], 'Géographie')
        self.assertIn('license_nom', row['source'])

    def test_search_et_filtres(self):
        data = self.api_get('/api/v1/datasets/?search=villages')
        self.assertEqual([row['slug'] for row in data['results']], ['sen-villages'])
        data = self.api_get('/api/v1/datasets/?categorie=demographie')
        self.assertEqual([row['slug'] for row in data['results']], ['sen-population-admin'])
        data = self.api_get('/api/v1/datasets/?source__slug=galsenify')
        self.assertGreaterEqual(len(data['results']), 3)

    def test_detail_expose_versions_et_qualite(self):
        data = self.api_get('/api/v1/datasets/sen-admin-boundaries/')
        self.assertEqual(len(data['versions']), 1)
        self.assertEqual(data['versions'][0]['version_number'], '1.0.0')
        self.assertIn('latest_quality_report', data)
        self.assertIsNotNone(data['latest_quality_report'])
        self.assertIn('methodology', data)

    def test_action_sources(self):
        data = self.api_get('/api/v1/datasets/sources/')
        slugs = {row['slug'] for row in data}
        self.assertEqual(slugs, {'hdx-cod-ab', 'galsenify'})

    def test_download_csv_content_type_et_header(self):
        response = self.client.get('/api/v1/datasets/sen-villages/download/?format=csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn('sen-villages.csv', response['Content-Disposition'])
        body = response.content.decode('utf-8-sig')
        first_line = body.splitlines()[0]
        self.assertEqual(first_line, 'nom,region')

    def test_download_json(self):
        response = self.client.get('/api/v1/datasets/sen-communes/download/?format=json')
        self.assertEqual(response.status_code, 200)
        rows = json.loads(response.content.decode('utf-8'))
        self.assertIsInstance(rows, list)
        if rows:
            self.assertEqual(set(rows[0].keys()), {'nom', 'type', 'departement'})

    def test_download_geojson_feature_collection(self):
        response = self.client.get(
            '/api/v1/datasets/sen-admin-boundaries/download/?format=geojson'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['type'], 'FeatureCollection')
        self.assertGreaterEqual(len(data['features']), 1)

    def test_format_inconnu_400(self):
        response = self.client.get('/api/v1/datasets/sen-villages/download/?format=xml')
        self.assertEqual(response.status_code, 400)

    def test_slug_inconnu_404(self):
        response = self.client.get('/api/v1/datasets/inconnu/download/?format=json')
        self.assertEqual(response.status_code, 404)

    def test_build_download_exporteur_manquant(self):
        dataset = Dataset.objects.get(slug='sen-universites')
        self.assertIsNone(build_download(dataset, 'geojson'))


class ExportersTests(TestCase):
    def setUp(self):
        build_geo_data()
        call_command('sync_datasets', verbosity=0)

    def test_admin_csv_rows(self):
        from datasets.exporters import export_admin_boundaries_csv
        content, fmt = export_admin_boundaries_csv()
        self.assertEqual(fmt, 'csv')
        lines = content.splitlines()
        self.assertEqual(lines[0], 'pcode,nom,niveau,parent_pcode')
        self.assertIn(',region,', ','.join(lines))

    def test_population_admin_json(self):
        from datasets.exporters import export_population_admin
        content, fmt = export_population_admin('json')
        rows = json.loads(content)
        self.assertEqual(fmt, 'json')
        self.assertTrue(all(r['population'] is not None for r in rows))
