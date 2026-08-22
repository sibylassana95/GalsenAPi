import json
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase

from . import ingest
from .management.commands.fix_dataset_encoding import repair_json_bytes
from .models import (
    Arrondissement,
    Commune,
    Departement,
    Pays,
    Region,
    Village,
)
from .utils import repair_mojibake, slug_nom

FIXTURES_DIR = Path(__file__).parent / 'tests' / 'fixtures'


def load_fixture_features():
    data = json.loads((FIXTURES_DIR / 'test_codab.json').read_bytes())
    return {level: data[f'adm{level}']['features'] for level in (1, 2, 3)}


class UtilsTests(TestCase):
    def test_slug_nom_accents_casse(self):
        self.assertEqual(slug_nom('Kédougou'), 'kedougou')
        self.assertEqual(slug_nom('THIÈS'), 'thies')
        self.assertEqual(slug_nom('Saint-Louis'), 'saint-louis')
        self.assertEqual(slug_nom('Guédiawaye'), 'guediawaye')

    def test_repair_mojibake(self):
        self.assertEqual(repair_mojibake('Ã©cole'), 'école')
        self.assertIsNone(repair_mojibake('Sénégal'))
        self.assertIsNone(repair_mojibake('Touba Ndaw\x8fne'))

    def test_repair_json_bytes_idempotent(self):
        raw = json.dumps({'nom': 'SÃ©nÃ©gal'}, ensure_ascii=False).encode('utf-8')
        new_content, stats = repair_json_bytes(raw)
        self.assertIsNotNone(new_content)
        self.assertEqual(stats['repaires'], 1)
        repaired = json.loads(new_content.decode('utf-8'))
        self.assertEqual(repaired['nom'], 'Sénégal')
        new_content_2, stats_2 = repair_json_bytes(new_content)
        self.assertIsNone(new_content_2)
        self.assertEqual(stats_2['repaires'], 0)


class HierarchyTests(TestCase):
    def build_hierarchy(self):
        pays = Pays.objects.create(nom='Sénégal', code_iso2='SN')
        region = Region.objects.create(
            pays=pays, pcode='SN01', nom='Dakar', latitude='14.7', longitude='-17.4'
        )
        departement = Departement.objects.create(region=region, pcode='SN011', nom='Dakar')
        arrondissement = Arrondissement.objects.create(
            departement=departement, pcode='SN0111', nom='Almadies'
        )
        commune = Commune.objects.create(departement=departement, nom='Yoff')
        village = Village.objects.create(region=region, commune=commune, nom='Ngor')
        return pays, region, departement, arrondissement, commune, village

    def test_hierarchy_creation_and_str(self):
        pays, region, dept, arrdt, commune, village = self.build_hierarchy()
        self.assertEqual(str(pays), 'Sénégal')
        self.assertEqual(str(region), 'Dakar')
        self.assertEqual(str(dept), 'Dakar')
        self.assertEqual(str(arrdt), 'Almadies')
        self.assertEqual(str(commune), 'Yoff')
        self.assertEqual(str(village), 'Ngor')
        self.assertEqual(region.pays, pays)
        self.assertEqual(list(pays.regions.all()), [region])
        self.assertEqual(list(region.departements.all()), [dept])
        self.assertEqual(list(dept.arrondissements.all()), [arrdt])
        self.assertEqual(list(dept.communes.all()), [commune])
        self.assertEqual(list(region.villages.all()), [village])

    def test_ordering_par_nom(self):
        pays = Pays.objects.create()
        Region.objects.create(pays=pays, pcode='SN02', nom='Ziguinchor')
        Region.objects.create(pays=pays, pcode='SN01', nom='Dakar')
        self.assertEqual(list(Region.objects.values_list('nom', flat=True)),
                         ['Dakar', 'Ziguinchor'])

    def test_pcode_unique(self):
        pays = Pays.objects.create()
        Region.objects.create(pays=pays, pcode='SN01', nom='Dakar')
        with self.assertRaises(IntegrityError):
            Region.objects.create(pays=pays, pcode='SN01', nom='Thiès')

    def test_departement_region_nom_unique(self):
        pays = Pays.objects.create()
        region = Region.objects.create(pays=pays, pcode='SN01', nom='Dakar')
        Departement.objects.create(region=region, pcode='SN011', nom='Rufisque')
        with self.assertRaises(IntegrityError):
            Departement.objects.create(region=region, pcode='SN012', nom='Rufisque')


class ImportCodabTests(TestCase):
    def import_fixture(self):
        report = ingest.ImportReport()
        counts = ingest.import_codab(load_fixture_features(), report)
        return counts, report

    def test_import_hierarchie_et_centroide(self):
        counts, _ = self.import_fixture()
        self.assertEqual(counts['regions_crees'], 1)
        self.assertEqual(counts['departements_crees'], 1)
        self.assertEqual(counts['arrondissements_crees'], 1)

        region = Region.objects.get(pcode='TEST01')
        self.assertEqual(region.nom, 'Région Test')
        self.assertEqual(region.meta['license'], ingest.LICENSE)
        self.assertEqual(region.meta['release_date'], '2024-05-20')
        self.assertEqual(json.loads(json.dumps(region.geometry))['type'], 'MultiPolygon')
        self.assertAlmostEqual(float(region.latitude), 14.46, places=5)
        self.assertAlmostEqual(float(region.longitude), -16.04, places=5)

        departement = Departement.objects.get(pcode='TEST0102')
        self.assertEqual(departement.region.pcode, 'TEST01')
        arrondissement = Arrondissement.objects.get(pcode='TEST010201')
        self.assertEqual(arrondissement.departement.pcode, 'TEST0102')

    def test_import_idempotent(self):
        first, _ = self.import_fixture()
        second, _ = self.import_fixture()
        self.assertEqual(first['regions_crees'], 1)
        self.assertEqual(second['regions_crees'], 0)
        self.assertEqual(second['departements_maj'], 1)
        self.assertEqual(Region.objects.count(), 1)
        self.assertEqual(Departement.objects.count(), 1)
        self.assertEqual(Arrondissement.objects.count(), 1)


class ImportLegacyTests(TestCase):
    def setUp(self):
        report = ingest.ImportReport()
        ingest.import_codab(load_fixture_features(), report)

    def test_communes_et_villages(self):
        legacy_communes = [
            {'nom': 'Département Test', 'region': 'RÉGION TEST'},
            {'nom': 'Inconnue', 'region': 'RÉGION TEST'},
            {'nom': 'Orpheline', 'region': 'NULLE PART'},
        ]
        legacy_villages = [
            {'nom': 'Keur Test, Région Test', 'region': 'REGION TEST'},
            {'nom': 'Keur Test, Région Test', 'region': 'REGION TEST'},
            {'nom': 'Sans région', 'region': 'INCONNU'},
        ]
        with patch.object(ingest, '_load_legacy',
                          side_effect=[legacy_communes, legacy_villages, [], []]):
            report = ingest.ImportReport()
            ingest.import_legacy(report)

        self.assertEqual(report.counts['communes_creees'], 1)
        self.assertEqual(report.counts['communes_non_resolues'], 2)
        self.assertEqual(report.counts['villages_crees'], 1)
        self.assertEqual(report.counts['villages_doublons'], 1)
        self.assertEqual(report.counts['villages_non_resolus'], 1)

        commune = Commune.objects.get()
        self.assertEqual(commune.nom, 'Département Test')
        self.assertEqual(commune.departement.pcode, 'TEST0102')
        village = Village.objects.get()
        self.assertEqual(village.nom, 'Keur Test')
        self.assertEqual(village.region.pcode, 'TEST01')
        self.assertIsNone(village.commune)

    def test_departements_population_superficie_legacy(self):
        legacy_departements = [
            {'nom': 'Département Test', 'region': 'RÉGION TEST',
             'population': 123456, 'superficie': 789},
            {'nom': 'Inconnu', 'region': 'NULLE PART',
             'population': 1, 'superficie': 2},
        ]
        with patch.object(ingest, '_load_legacy',
                          side_effect=[[], [], [], legacy_departements]):
            report = ingest.ImportReport()
            ingest.import_legacy(report)

        departement = Departement.objects.get(pcode='TEST0102')
        self.assertEqual(departement.population, 123456)
        self.assertEqual(departement.superficie_km2, Decimal('789'))
        self.assertEqual(departement.meta['population_source'],
                         'legacy_departments.json')
        self.assertEqual(report.counts['departements_renseignes_legacy'], 1)
        self.assertEqual(report.counts['departements_legacy_non_resolus'], 1)

        with patch.object(ingest, '_load_legacy',
                          side_effect=[[], [], [], legacy_departements]):
            second = ingest.import_legacy(ingest.ImportReport())
        self.assertEqual(second['departements_renseignes'], 1)
        self.assertEqual(Departement.objects.count(), 1)
        departement.refresh_from_db()
        self.assertEqual(departement.population, 123456)

    def test_regions_population_code_court_legacy(self):
        legacy_regions = [
            {'nom': 'RÉGION TEST', 'code': 'RT',
             'population': 4042225, 'superficie': 547},
            {'nom': 'Inconnue', 'code': 'XX', 'population': 1, 'superficie': 2},
        ]
        with patch.object(ingest, '_load_legacy',
                          side_effect=[[], [], legacy_regions, []]):
            report = ingest.ImportReport()
            ingest.import_legacy(report)

        region = Region.objects.get(pcode='TEST01')
        self.assertEqual(region.population, 4042225)
        self.assertEqual(region.superficie_km2, Decimal('547'))
        self.assertEqual(region.code_court, 'RT')
        self.assertEqual(region.meta['population_source'], 'legacy_regions.json')
        self.assertEqual(report.counts['regions_renseignees_legacy'], 1)
        self.assertEqual(report.counts['regions_legacy_non_resolues'], 1)

        # Idempotence + code_court déjà renseigné non écrasé
        legacy_regions_bis = [
            {'nom': 'Region Test', 'code': 'ZZ',
             'population': 4042225, 'superficie': 547},
        ]
        with patch.object(ingest, '_load_legacy',
                          side_effect=[[], [], legacy_regions_bis, []]):
            second = ingest.import_legacy(ingest.ImportReport())
        self.assertEqual(second['regions_renseignees'], 1)
        region.refresh_from_db()
        self.assertEqual(region.population, 4042225)
        self.assertEqual(region.code_court, 'RT')
        self.assertEqual(Region.objects.count(), 1)


class GeoApiTests(TestCase):
    def setUp(self):
        pays = Pays.objects.create(nom='Sénégal', code_iso2='SN')
        self.region_dakar = Region.objects.create(
            pays=pays, pcode='SN01', nom='Dakar', code_court='DK',
            chef_lieu='Dakar', population=3100000, superficie_km2='1831.00',
            latitude='14.716667', longitude='-17.466667',
            geometry={'type': 'Polygon', 'coordinates': [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
        )
        Region.objects.create(
            pays=pays, pcode='SN02', nom='Ziguinchor', population=600000,
        )
        Departement.objects.create(region=self.region_dakar, pcode='SN011', nom='Dakar',
                                   population=100000, superficie_km2='79.00')
        Departement.objects.create(region=self.region_dakar, pcode='SN012', nom='Rufisque',
                                   population=200000, superficie_km2='372.00')
        departement_zig = Departement.objects.create(
            region=Region.objects.get(pcode='SN02'), pcode='SN021', nom='Ziguinchor'
        )
        Arrondissement.objects.create(departement=departement_zig, pcode='SN0211', nom='Niaguis')
        commune_yoff = Commune.objects.create(departement=departement_zig, nom='Yoff')
        Village.objects.create(region=self.region_dakar, commune=commune_yoff,
                               nom='Ngor', population=5000)
        Village.objects.create(region=self.region_dakar, nom='Dakar Plateau', population=12000)

    def api_get(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)
        return response.json()

    def test_pays_objet_unique(self):
        data = self.api_get('/api/v1/pays/')
        self.assertEqual(data['code_iso2'], 'SN')
        self.assertNotIn('results', data)

    def test_envelope_pagination_regions(self):
        data = self.api_get('/api/v1/regions/?page_size=5')
        for key in ('count', 'next', 'previous', 'results'):
            self.assertIn(key, data)
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['results']), 2)

    def test_filtre_departements_par_region(self):
        data = self.api_get('/api/v1/departements/?region=SN01')
        self.assertEqual(data['count'], 2)
        self.assertEqual({row['pcode'] for row in data['results']}, {'SN011', 'SN012'})
        self.assertTrue(all(row['region'] == 'SN01' for row in data['results']))

    def test_detail_region_par_pcode_avec_departements(self):
        data = self.api_get('/api/v1/regions/SN01/')
        self.assertEqual(data['nom'], 'Dakar')
        self.assertEqual([d['pcode'] for d in data['departements']], ['SN011', 'SN012'])
        self.assertNotIn('meta', data)

    def test_detail_region_inconnue_404(self):
        response = self.client.get('/api/v1/regions/SN99/')
        self.assertEqual(response.status_code, 404)

    def test_regions_geojson_feature_collection(self):
        data = self.api_get('/api/v1/regions/geojson/')
        self.assertEqual(data['type'], 'FeatureCollection')
        self.assertGreaterEqual(len(data['features']), 1)
        feature = data['features'][0]
        self.assertEqual(feature['type'], 'Feature')
        self.assertIn('pcode', feature['properties'])
        pcodes = {feature['properties']['pcode'] for feature in data['features']}
        self.assertEqual(pcodes, {'SN01'})

    def test_departements_geojson(self):
        data = self.api_get('/api/v1/departements/geojson/?region=SN01')
        self.assertEqual(data['type'], 'FeatureCollection')

    def test_villages_search_partiel(self):
        data = self.api_get('/api/v1/villages/?search=dak&page_size=10')
        noms = [row['nom'] for row in data['results']]
        self.assertEqual(noms, ['Dakar Plateau'])

    def test_ordering_population_desc(self):
        data = self.api_get('/api/v1/regions/?ordering=-population')
        populations = [row['population'] for row in data['results']]
        self.assertEqual(populations, sorted(populations, reverse=True))
        self.assertEqual(populations[0], 3100000)

    def test_departements_ordering_population_desc(self):
        data = self.api_get('/api/v1/departements/?ordering=-population')
        pcodes = [row['pcode'] for row in data['results']]
        self.assertEqual(pcodes[:2], ['SN012', 'SN011'])

    def test_departements_champs_population_serialises(self):
        data = self.api_get('/api/v1/departements/SN011/')
        self.assertEqual(data['population'], 100000)
        self.assertEqual(data['superficie_km2'], '79.00')


class FixEncodingCommandTests(TestCase):
    def test_command_sur_dataset_propre_ne_reecrit_pas(self):
        from geo.management.commands.fix_dataset_encoding import TARGET_FILES
        before = {
            name: (Path('dataset') / f'{name}.json').read_bytes()
            for name in TARGET_FILES
            if (Path('dataset') / f'{name}.json').exists()
        }
        call_command('fix_dataset_encoding', verbosity=0)
        after = {
            name: (Path('dataset') / f'{name}.json').read_bytes()
            for name in TARGET_FILES
            if (Path('dataset') / f'{name}.json').exists()
        }
        self.assertEqual(before, after)
