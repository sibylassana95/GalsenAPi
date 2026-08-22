import json
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
                          side_effect=[legacy_communes, legacy_villages]):
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
