import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase

from datasets.models import DataSource
from geo.models import Departement, Pays, Region
from geo.statistics import (
    POPULATION_SOURCE_NOTE,
    build_statistics,
    population_source_note,
)

from .models import PopulationRecord

FIXTURE = Path(__file__).parent / 'tests' / 'fixtures' / 'mini_rgph5.json'


class BaseDemographieTestCase(TestCase):
    def setUp(self):
        cache.clear()
        pays = Pays.objects.create(nom='Sénégal', code_iso2='SN')
        self.dakar = Region.objects.create(pays=pays, pcode='SN01', nom='Dakar')
        self.thies = Region.objects.create(pays=pays, pcode='SN13', nom='Thiès')
        self.dept_dakar = Departement.objects.create(
            region=self.dakar, pcode='SN0101', nom='Dakar'
        )
        # Slug volontairement différent de « Malem Hoddar » (alias à résoudre).
        self.dept_malem = Departement.objects.create(
            region=self.thies, pcode='SN1304', nom='Malem-Hodar'
        )

    def run_import(self, fichier=FIXTURE, **options):
        out = StringIO()
        call_command('import_demographie', fichier=str(fichier), stdout=out, **options)
        return out.getvalue()


class ImportDemographieTests(BaseDemographieTestCase):
    def test_import_upsert_refresh_geo_et_stats(self):
        self.assertEqual(population_source_note(), POPULATION_SOURCE_NOTE)
        output = self.run_import()

        self.assertEqual(PopulationRecord.objects.count(), 4)
        record_dakar = PopulationRecord.objects.get(
            entity_type='region', region=self.dakar, annee=2023
        )
        self.assertEqual(record_dakar.population, 1000)
        self.assertEqual(record_dakar.hommes, 600)
        self.assertEqual(record_dakar.femmes, 400)
        self.assertEqual(record_dakar.value_type, 'officielle')
        self.assertEqual(record_dakar.source.slug, 'ansd')
        self.assertIn('I-21', record_dakar.meta['tableau'])

        self.dakar.refresh_from_db()
        self.assertEqual(self.dakar.population, 1000)
        self.assertEqual(self.dakar.meta['population_source'], 'RGPH-5 2023 (ANSD)')
        self.dept_dakar.refresh_from_db()
        self.assertEqual(self.dept_dakar.population, 700)
        self.assertEqual(
            self.dept_dakar.meta['population_source'], 'RGPH-5 2023 (ANSD)'
        )

        record_dept = PopulationRecord.objects.get(
            entity_type='departement', departement=self.dept_malem
        )
        self.assertIn('I-9', record_dept.meta['tableau'])

        stats = build_statistics()
        self.assertEqual(stats['population']['source_note'], 'RGPH-5 2023 (ANSD)')
        self.assertEqual(stats['population']['totale'], 1500)
        self.assertEqual(stats['population']['plus_peuplee']['pcode'], 'SN01')

    def test_alias_departement_malem_hoddar(self):
        self.run_import()
        record = PopulationRecord.objects.get(
            entity_type='departement', departement=self.dept_malem
        )
        self.assertEqual(record.population, 120)

    def test_import_idempotent(self):
        self.run_import()
        PopulationRecord.objects.update(population=42)
        self.dakar.population = 999
        self.dakar.save(update_fields=['population'])

        self.run_import()

        self.assertEqual(PopulationRecord.objects.count(), 4)
        record_dakar = PopulationRecord.objects.get(
            entity_type='region', region=self.dakar, annee=2023
        )
        self.assertEqual(record_dakar.population, 1000)
        self.dakar.refresh_from_db()
        self.assertEqual(self.dakar.population, 1000)

    def test_no_refresh_geo(self):
        self.run_import(no_refresh_geo=True)
        self.dakar.refresh_from_db()
        self.assertIsNone(self.dakar.population)
        self.assertNotIn('population_source', self.dakar.meta or {})
        self.assertTrue(PopulationRecord.objects.filter(entity_type='region').exists())

    def test_entites_manquantes_signalees(self):
        with TemporaryDirectory() as tmp:
            data = json.loads(FIXTURE.read_bytes())
            data['regions'].append({'nom': 'Atlantide', 'population': 1})
            path = Path(tmp) / 'incomplet.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            output = self.run_import(fichier=path)
        self.assertIn('NON résolues', output)
        self.assertIn('Atlantide', output)
        # Seuls les 4 enregistrements résolus du fichier doivent exister.
        self.assertEqual(PopulationRecord.objects.count(), 4)

    def test_fichier_inexistant_erreur(self):
        from django.core.management import CommandError

        with self.assertRaises(CommandError):
            self.run_import(fichier='nulle_part/inexistant.json')

    def test_contrainte_unicite_entite_annee(self):
        source = DataSource.objects.create(
            nom='ANSD', slug='ansd', url='https://www.ansd.sn',
            license_nom='CC BY 4.0',
        )
        PopulationRecord.objects.create(
            entity_type='region', region=self.dakar, annee=2023,
            population=1000, source=source,
        )
        with self.assertRaises(IntegrityError):
            PopulationRecord.objects.create(
                entity_type='region', region=self.dakar, annee=2023,
                population=2000, source=source,
            )

    def test_clean_incoherences_fk(self):
        source = DataSource.objects.create(
            nom='ANSD', slug='ansd-bis', url='https://www.ansd.sn',
            license_nom='CC BY 4.0',
        )
        with self.assertRaises(ValidationError):
            PopulationRecord(
                entity_type='departement', departement=self.dept_dakar,
                annee=2023, population=1, source=source,
            ).full_clean()
        with self.assertRaises(ValidationError):
            PopulationRecord(
                entity_type='region', departement=self.dept_dakar,
                annee=2023, population=1, source=source,
            ).full_clean()


class DemographieApiTests(BaseDemographieTestCase):
    URL = '/api/v1/demographie/population/'

    def setUp(self):
        super().setUp()
        self.run_import()

    def api_get(self, query=''):
        response = self.client.get(self.URL + query)
        self.assertEqual(response.status_code, 200, self.URL + query)
        return response.json()

    def test_liste_par_defaut_ordering_population_decroissante(self):
        data = self.api_get('?annee=2023&ordering=-population')
        populations = [row['population'] for row in data['results']]
        self.assertEqual(populations, sorted(populations, reverse=True))
        premier = data['results'][0]
        self.assertEqual(premier['entite_nom'], 'Dakar')
        self.assertEqual(premier['entity_type'], 'region')
        self.assertEqual(premier['entite_pcode'], 'SN01')
        self.assertEqual(premier['region_pcode'], 'SN01')
        self.assertEqual(premier['region_nom'], 'Dakar')
        self.assertEqual(data['count'], PopulationRecord.objects.count())

    def test_filtre_niveau_region_top3_ordre_attendu(self):
        data = self.api_get('?niveau=region&ordering=-population')
        noms = [row['entite_nom'] for row in data['results']]
        self.assertEqual(noms[0], 'Dakar')
        self.assertEqual(len(noms), 2)
        for row in data['results']:
            self.assertEqual(row['entity_type'], 'region')
            self.assertIn('hommes', row)

    def test_filtre_niveau_departement_avec_region_parente(self):
        data = self.api_get('?niveau=departement&region=SN01&ordering=-population')
        self.assertEqual(data['count'], 1)
        row = data['results'][0]
        self.assertEqual(row['entite_nom'], 'Dakar')
        self.assertEqual(row['entite_pcode'], 'SN0101')
        self.assertEqual(row['region_pcode'], 'SN01')
        self.assertEqual(row['region_nom'], 'Dakar')

    def test_filtre_niveau_departement_via_pcode_region_lui_meme(self):
        data = self.api_get('?niveau=region&region=SN13')
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['entite_nom'], 'Thiès')

    def test_filtre_annee(self):
        data = self.api_get('?annee=2023')
        self.assertEqual(data['count'], 4)
        reponse_annee_invalide = self.client.get(self.URL + '?annee=deuxmille')
        self.assertEqual(reponse_annee_invalide.status_code, 400)

    def test_niveau_invalide_400(self):
        response = self.client.get(self.URL + '?niveau=village')
        self.assertEqual(response.status_code, 400)
        self.assertIn('niveau', response.json())

    def test_region_inconnue_404(self):
        response = self.client.get(self.URL + '?region=SN99')
        self.assertEqual(response.status_code, 404)
