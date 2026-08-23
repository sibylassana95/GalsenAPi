import json
import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.core.management import call_command, CommandError
from django.db import IntegrityError
from django.test import TestCase

from datasets.models import DataSource
from economie.models import IndicateurEconomique, ObservationEconomique
from economie.worldbank import importer_indicateur, parse_reponse

CODE_PIB = 'NY.GDP.MKTP.CD'
CODE_INFLATION = 'FP.CPI.TOTL.ZG'


def payload_wb(code=CODE_PIB, nom_officiel='GDP (current US$)',
               lastupdated='2026-07-13'):
    """Reponse JSON type World Bank : [[meta], [data...]] avec des nulls."""
    lignes = [
        # (date, value, decimal)
        ('2025', '37006536238.3731', '0'),
        ('2024', '32169996051.8502', '0'),
        ('2023', None, '0'),
        ('2022', '27783332222.6759', '0'),
        ('1961', None, '1'),
        ('1960', '1240000000', '1'),
    ]
    data = [
        {
            'indicator': {'id': code, 'value': nom_officiel},
            'country': {'id': 'SN', 'value': 'Senegal'},
            'countryiso3code': 'SEN',
            'date': date,
            'value': value,
            'unit': '',
            'obs_status': '',
            'decimal': dec,
        }
        for date, value, dec in lignes
    ]
    meta = {
        'page': 1, 'pages': 14, 'per_page': 25000,
        'total': len(data), 'sourceid': '2', 'lastupdated': lastupdated,
    }
    return [meta, data]


def ecrire_fixture_cache(tmp_dir, code, payload):
    path = Path(tmp_dir) / f'{code}.json'
    path.write_text(json.dumps(payload), encoding='utf-8')
    return path


class PipelineWorldbankTests(TestCase):
    def setUp(self):
        self.source = DataSource.objects.create(
            nom='Banque mondiale', slug='worldbank',
            url='https://data.worldbank.org', license_nom='CC BY 4.0',
        )

    def _importer(self, code=CODE_PIB, payload=None):
        payload = payload if payload is not None else payload_wb(code=code)
        return importer_indicateur(
            code, parse_reponse(payload), source=self.source,
            api_url=f'https://api.worldbank.org/v2/country/SEN/indicator/{code}',
        )

    def test_parse_ecarte_les_nulls(self):
        parse = parse_reponse(payload_wb())
        self.assertEqual(set(parse['valeurs']), {2025, 2024, 2022, 1960})
        self.assertEqual(parse['total_lignes'], 6)
        self.assertEqual(parse['nom_officiel'], 'GDP (current US$)')
        self.assertEqual(parse['decimal'], '0')

    def test_import_upsert_indicateur_et_observations(self):
        indicateur, stats = self._importer()

        self.assertEqual(indicateur.code, CODE_PIB)
        self.assertEqual(indicateur.nom, 'PIB courant')
        self.assertEqual(indicateur.nom_officiel, 'GDP (current US$)')
        self.assertEqual(indicateur.categorie, 'pib')
        self.assertEqual(indicateur.unite, 'US$')
        self.assertEqual(indicateur.decimal, '0')
        self.assertEqual(indicateur.source.slug, 'worldbank')
        self.assertTrue(indicateur.meta['api_url'].startswith(
            'https://api.worldbank.org/v2/country/SEN/indicator/'
        ))
        self.assertIn('downloaded_at', indicateur.meta)

        # Les 2 nulls du payload sont ecartes.
        self.assertEqual(ObservationEconomique.objects.count(), 4)
        self.assertEqual(stats['crees'], 4)
        self.assertEqual(stats['sans_donnee'], 2)
        self.assertEqual(stats['an_min'], 1960)
        self.assertEqual(stats['an_max'], 2025)

        derniere = ObservationEconomique.objects.get(
            indicateur=indicateur, annee=2025
        )
        self.assertEqual(
            derniere.valeur, Decimal('37006536238.373100')
        )

    def test_import_idempotent(self):
        self._importer()
        obs = ObservationEconomique.objects.get(annee=2022)
        obs.valeur = Decimal('1.000000')
        obs.save(update_fields=['valeur'])

        _, stats = self._importer()

        self.assertEqual(IndicateurEconomique.objects.count(), 1)
        self.assertEqual(ObservationEconomique.objects.count(), 4)
        self.assertEqual(stats['crees'], 0)
        obs.refresh_from_db()
        self.assertEqual(obs.valeur, Decimal('27783332222.675900'))

    def test_code_hors_curateur_refuse(self):
        with self.assertRaises(ValueError):
            self._importer(code='XX.FAKE.CODE')

    def test_parse_reponse_invalide_leve_valueerror(self):
        with self.assertRaises(ValueError):
            parse_reponse([{'total': 0}, None])
        with self.assertRaises(ValueError):
            parse_reponse({'erreur': True})

    def test_contrainte_unicite_indicateur_annee(self):
        indicateur, _ = self._importer()
        with self.assertRaises(IntegrityError):
            ObservationEconomique.objects.create(
                indicateur=indicateur, annee=2025, valeur=Decimal('1'),
            )


class CommandeImportEconomieTests(TestCase):
    def test_commande_offline_cache_et_idempotence(self):
        with tempfile.TemporaryDirectory() as tmp:
            ecrire_fixture_cache(tmp, CODE_PIB, payload_wb(code=CODE_PIB))
            ecrire_fixture_cache(tmp, CODE_INFLATION, payload_wb(
                code=CODE_INFLATION,
                nom_officiel='Inflation, consumer prices (annual %)',
            ))
            codes = f'{CODE_PIB},{CODE_INFLATION}'
            out = StringIO()
            call_command('import_economie', '--offline', '--cache-dir', tmp,
                         '--indicators', codes, stdout=out)
            sortie = out.getvalue()

            self.assertIn('Contrôle PIB : cohérent.', sortie)
            self.assertIn('37 006', sortie)
            self.assertIn('[2/2]', sortie)

            out2 = StringIO()
            call_command('import_economie', '--offline', '--cache-dir', tmp,
                         '--indicators', codes, stdout=out2)
            self.assertNotIn('créées 4', out2.getvalue())

        self.assertTrue(DataSource.objects.filter(slug='worldbank').exists())
        self.assertEqual(IndicateurEconomique.objects.count(), 2)
        self.assertEqual(ObservationEconomique.objects.count(), 8)

    def test_commande_code_inconnu(self):
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command('import_economie', '--indicators', 'XX.FAKE',
                         stdout=out)


class ApiEconomieTests(TestCase):
    URL_INDICATEURS = '/api/v1/economie/indicateurs/'
    URL_OBSERVATIONS = '/api/v1/economie/observations/'

    @classmethod
    def setUpTestData(cls):
        source = DataSource.objects.create(
            nom='Banque mondiale', slug='worldbank',
            url='https://data.worldbank.org', license_nom='CC BY 4.0',
        )
        for code, nom in (
            (CODE_PIB, 'GDP (current US$)'),
            (CODE_INFLATION, 'Inflation, consumer prices (annual %)'),
        ):
            importer_indicateur(
                code, parse_reponse(payload_wb(code=code, nom_officiel=nom)),
                source=source,
                api_url=f'https://api.worldbank.org/v2/country/SEN/indicator/{code}',
            )

    def api_get(self, url, query=''):
        response = self.client.get(url + query)
        self.assertEqual(response.status_code, 200, url + query)
        return response.json()

    def test_liste_indicateurs_avec_agregats(self):
        data = self.api_get(self.URL_INDICATEURS)
        self.assertEqual(data['count'], 2)
        pib = next(r for r in data['results'] if r['code'] == CODE_PIB)
        self.assertEqual(pib['nb_observations'], 4)
        self.assertEqual(pib['derniere_annee'], 2025)
        self.assertAlmostEqual(float(pib['derniere_valeur']), 37006536238.3731)
        self.assertEqual(pib['unite'], 'US$')
        self.assertEqual(pib['categorie'], 'pib')

    def test_filtre_categorie(self):
        data = self.api_get(self.URL_INDICATEURS, '?categorie=pib')
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['code'], CODE_PIB)

    def test_recherche_par_nom_officiel(self):
        data = self.api_get(self.URL_INDICATEURS, '?search=GDP')
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['code'], CODE_PIB)

    def test_detail_par_code(self):
        response = self.client.get(self.URL_INDICATEURS + CODE_PIB + '/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['nom'], 'PIB courant')

    def test_observations_filtre_indicateur(self):
        data = self.api_get(self.URL_OBSERVATIONS,
                            f'?indicateur={CODE_INFLATION}')
        self.assertEqual(data['count'], 4)
        annees = [row['annee'] for row in data['results']]
        self.assertEqual(annees, sorted(annees, reverse=True))

    def test_observations_filtres_annees_et_ordering(self):
        data = self.api_get(self.URL_OBSERVATIONS,
                            f'?indicateur={CODE_PIB}&annee_min=2022&'
                            f'annee_max=2024&ordering=annee')
        self.assertEqual([row['annee'] for row in data['results']],
                         [2022, 2024])

    def test_observations_ordering_valeur(self):
        data = self.api_get(self.URL_OBSERVATIONS,
                            f'?indicateur={CODE_PIB}&ordering=valeur')
        valeurs = [float(row['valeur']) for row in data['results']]
        self.assertEqual(valeurs, sorted(valeurs))

    def test_pagination_page_size(self):
        data = self.api_get(self.URL_OBSERVATIONS, '?page_size=3&page=1')
        self.assertEqual(len(data['results']), 3)
