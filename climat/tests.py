import csv as module_csv
import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from climat import ghcn
from climat.models import ObservationMensuelle, StationClimatique
from datasets.models import DataSource

STATION_YOFF = 'SG000061641'
STATION_ZIGUINCHOR = 'SGM00061695'


def ligne_inventaire(sid, lat, lon, elev, nom, gsn=''):
    """Ligne fixed-width ghcnd-stations.txt (ID 0-11, LAT 12-20,
    LON 21-30, ELEV 31-37, STATE 38-40, NAME 41-71, GSN 72-75)."""
    return (
        f'{sid:<11} {lat:>8} {lon:>9} {elev:>6}    '
        f'{nom:<30}{gsn:<3}'
    )


INVENTAIRE_FIXTURE = '\n'.join([
    ligne_inventaire(STATION_YOFF, '14.7330', '-17.5000', '24.0',
                     'DAKAR/YOFF', 'GSN'),
    ligne_inventaire(STATION_ZIGUINCHOR, '12.5560', '-16.2820', '22.9',
                     'ZIGUINCHOR'),
    ligne_inventaire('USW00013994', '38.7520', '-90.3830', '166.1',
                     'ST LOUIS LAMBERT INTL AP'),
    ligne_inventaire('SGX99999999', '15.0000', '-15.0000', '-999.9',
                     'ALTITUDE ABSENTE'),
]) + '\n'


ELEMENTS = ghcn.ELEMENTS


def ecrire_csv_ghcn(path, lignes, station_id=STATION_YOFF):
    """Écrit un CSV type GHCN access (valeurs en dixièmes, colonnes
    *_ATTRIBUTES). lignes : [{'date': 'AAAA-MM-JJ', 'PRCP': '...', ...}]"""
    entetes = ['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'ELEVATION',
               'NAME']
    for element in ELEMENTS:
        entetes += [element, f'{element}_ATTRIBUTES']
    with open(path, 'w', newline='', encoding='utf-8') as fichier:
        writer = module_csv.writer(fichier, quoting=module_csv.QUOTE_ALL)
        writer.writerow(entetes)
        for ligne in sorted(lignes, key=lambda li: li['date']):
            cells = [station_id, ligne['date'], '14.733', '-17.5', '24.0',
                     'DAKAR YOFF, SG']
            for element in ELEMENTS:
                valeur = str(ligne.get(element, '') or '')
                cells += [valeur, 'H,,S' if valeur else '']
            writer.writerow(cells)


def jours_janvier_2020():
    """Cas connu : 3 jours documentés en janvier 2020."""
    return [
        {'date': '2020-01-01', 'PRCP': '0', 'TAVG': '223', 'TMIN': '180',
         'TMAX': '280'},
        # Valeurs avec padding espaces comme dans les vrais fichiers.
        {'date': '2020-01-02', 'PRCP': ' 120', 'TAVG': ' 225',
         'TMIN': ' 182', 'TMAX': ' 282'},
        {'date': '2020-01-03', 'TAVG': '227', 'TMIN': '184',
         'TMAX': '284'},
    ]


class ParseStationsTests(TestCase):
    def test_filtre_prefixe_pays_sg(self):
        stations = ghcn.parse_stations(INVENTAIRE_FIXTURE)
        ids = [s['station_id'] for s in stations]
        self.assertEqual(
            ids, [STATION_YOFF, STATION_ZIGUINCHOR, 'SGX99999999'],
        )
        self.assertNotIn('USW00013994', ids)

    def test_champs_fixed_width(self):
        yoff = ghcn.parse_stations(INVENTAIRE_FIXTURE)[0]
        self.assertEqual(yoff['station_id'], STATION_YOFF)
        self.assertEqual(yoff['nom'], 'Dakar/Yoff')
        self.assertEqual(yoff['latitude'], Decimal('14.7330'))
        self.assertEqual(yoff['longitude'], Decimal('-17.5000'))
        self.assertEqual(yoff['altitude'], Decimal('24.0'))

    def test_altitude_absente_devient_none(self):
        station = ghcn.parse_stations(INVENTAIRE_FIXTURE)[-1]
        self.assertIsNone(station['altitude'])


class ParsingDixiemesTests(TestCase):
    def test_conversion_dixiemes_vers_unites(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f'{STATION_YOFF}.csv'
            ecrire_csv_ghcn(path, jours_janvier_2020())
            lignes = ghcn.parser_journalier(path)

        self.assertEqual(len(lignes), 3)
        premiere = lignes[0]
        self.assertEqual(premiere['annee'], 2020)
        self.assertEqual(premiere['mois'], 1)
        self.assertEqual(premiere['valeurs']['TAVG'], Decimal('22.3'))
        self.assertEqual(premiere['valeurs']['TMAX'], Decimal('28.0'))
        self.assertEqual(premiere['valeurs']['PRCP'], Decimal('0.0'))
        deuxieme = lignes[1]
        self.assertEqual(deuxieme['valeurs']['PRCP'], Decimal('12.0'))
        self.assertEqual(deuxieme['valeurs']['TAVG'], Decimal('22.5'))

    def test_ligne_sans_valeur_exploitable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f'{STATION_YOFF}.csv'
            ecrire_csv_ghcn(path, [
                {'date': '2020-02-01'},  # toutes colonnes vides
                *jours_janvier_2020(),
            ])
            lignes = ghcn.parser_journalier(path)

        vide = [li for li in lignes if li['mois'] == 2][0]
        self.assertEqual(vide['valeurs'], {})


class AgregationMensuelleTests(TestCase):
    def _agrege(self, lignes, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f'{STATION_YOFF}.csv'
            ecrire_csv_ghcn(path, lignes)
            journalier = ghcn.parser_journalier(path)
            return ghcn.agreer_mensuel(journalier, **kwargs)

    def test_moyennes_somme_nb_jours_exactes(self):
        agrege = self._agrege(jours_janvier_2020())

        self.assertIn((2020, 1), agrege)
        janvier = agrege[(2020, 1)]
        self.assertEqual(janvier['tavg'], Decimal('22.50'))  # (22.3+22.5+22.7)/3
        self.assertEqual(janvier['tmin'], Decimal('18.20'))  # (18.0+18.2+18.4)/3
        self.assertEqual(janvier['tmax'], Decimal('28.20'))
        self.assertEqual(janvier['prcp_mm'], Decimal('12.00'))  # 0 + 12.0
        self.assertEqual(janvier['nb_jours'], 3)

    def test_mois_present_sans_mesure_null_et_zero_jours(self):
        agrege = self._agrege([
            *jours_janvier_2020(),
            {'date': '2020-02-01'},  # présent mais sans valeur
        ])
        fevrier = agrege[(2020, 2)]
        self.assertIsNone(fevrier['tavg'])
        self.assertIsNone(fevrier['prcp_mm'])
        self.assertEqual(fevrier['nb_jours'], 0)

    def test_mois_absent_non_cree(self):
        agrege = self._agrege([*jours_janvier_2020(),
                               {'date': '2018-07-15', 'PRCP': '500'}])
        self.assertNotIn((2020, 3), agrege)

    def test_from_annee_limite_historique(self):
        agrege = self._agrege([
            *jours_janvier_2020(),
            {'date': '2018-07-15', 'PRCP': '500', 'TAVG': '300'},
        ], from_annee=2019)
        self.assertEqual(list(agrege), [(2020, 1)])


class ImportUpsertTests(TestCase):
    def setUp(self):
        self.source = DataSource.objects.create(
            nom='NOAA NCEI — GHCN-Daily', slug='noaa-ghcn',
            url='https://www.ncei.noaa.gov', license_nom='Domaine public',
        )

    def _importer(self):
        station_data = ghcn.parse_stations(INVENTAIRE_FIXTURE)[0]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"{station_data['station_id']}.csv"
            ecrire_csv_ghcn(path, jours_janvier_2020(),
                            station_id=station_data['station_id'])
            agrege = ghcn.agreer_mensuel(ghcn.parser_journalier(path))
        return ghcn.importer_station(station_data, agrege,
                                     source=self.source)

    def test_import_station_et_observations(self):
        station, stats = self._importer()

        self.assertEqual(station.station_id, STATION_YOFF)
        self.assertTrue(station.meta['source_url'].endswith(
            f'/{STATION_YOFF}.csv'
        ))
        obs = ObservationMensuelle.objects.get(station=station,
                                               annee=2020, mois=1)
        self.assertEqual(obs.tavg, Decimal('22.50'))
        self.assertEqual(obs.prcp_mm, Decimal('12.00'))
        self.assertEqual(obs.nb_jours, 3)
        self.assertEqual(obs.source.slug, 'noaa-ghcn')
        self.assertEqual(stats['crees'], 1)

    def test_upsert_idempotent_restaure_les_valeurs_source(self):
        _, premier = self._importer()

        obs = ObservationMensuelle.objects.get(annee=2020, mois=1)
        obs.tavg = Decimal('99.99')
        obs.save(update_fields=['tavg'])

        _, second = self._importer()

        self.assertEqual(ObservationMensuelle.objects.count(), 1)
        self.assertEqual(StationClimatique.objects.count(), 1)
        self.assertEqual(second['crees'], 0)
        self.assertEqual(second['maj'], 1)
        obs.refresh_from_db()
        self.assertEqual(obs.tavg, Decimal('22.50'))


class CommandeImportClimatTests(TestCase):
    def test_commande_offline_idempotence_et_rapport(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / 'stations.txt').write_text(INVENTAIRE_FIXTURE,
                                                encoding='utf-8')
            ecrire_csv_ghcn(cache / f'{STATION_YOFF}.csv',
                            jours_janvier_2020())
            # Ziguinchor : CSV vide (aucune ligne) -> importé à zéro mois.
            ecrire_csv_ghcn(cache / f'{STATION_ZIGUINCHOR}.csv', [],
                            station_id=STATION_ZIGUINCHOR)
            ecrire_csv_ghcn(cache / 'SGX99999999.csv',
                            [{'date': '2020-02-15', 'PRCP': '30',
                              'TAVG': '310', 'TMIN': '250',
                              'TMAX': '360'}],
                            station_id='SGX99999999')

            out = StringIO()
            call_command('import_climat', '--offline', '--cache-dir', str(tmp),
                         '--from-annee', '2019', stdout=out)
            sortie = out.getvalue()

            self.assertIn('Stations Sénégal trouvées : 3', sortie)
            self.assertIn('[1/3]', sortie)
            self.assertIn('Plage années : 2020–2020', sortie)
            self.assertIn('Mois avec tavg : 1/1 (100 %)', sortie)
            self.assertIn('précipitations annuelles moyennes', sortie)

            self.assertEqual(StationClimatique.objects.count(), 3)
            self.assertEqual(ObservationMensuelle.objects.count(), 2)

            out2 = StringIO()
            call_command('import_climat', '--offline', '--cache-dir',
                         str(tmp), stdout=out2)
            self.assertNotIn('créés 1', out2.getvalue())
            self.assertIn('(maj)', out2.getvalue())

        self.assertTrue(
            DataSource.objects.filter(slug='noaa-ghcn').exists()
        )
        self.assertEqual(StationClimatique.objects.count(), 3)


class ControleRealismeTests(TestCase):
    def test_anomalie_signalee_hors_plage(self):
        agrege = {}
        for jour in range(1, 29):
            agrege[(2020, 1)] = {
                'tavg': Decimal('45.00'), 'tmin': Decimal('40.00'),
                'tmax': Decimal('50.00'), 'prcp_mm': Decimal('90000.00'),
                'nb_jours': 28,
            }
            break
        controles = ghcn.controle_realisme(agrege)
        self.assertEqual(len(controles['anomalies']), 2)

    def test_valeurs_plausibles_pas_anomalie(self):
        controles = ghcn.controle_realisme({
            (2020, 1): {
                'tavg': Decimal('26.00'), 'tmin': Decimal('20.00'),
                'tmax': Decimal('32.00'), 'prcp_mm': Decimal('50.00'),
                'nb_jours': 28,
            },
        })
        self.assertEqual(controles['anomalies'], [])


class ApiClimatTests(TestCase):
    URL_STATIONS = '/api/v1/climat/stations/'
    URL_OBSERVATIONS = '/api/v1/climat/observations/'

    @classmethod
    def setUpTestData(cls):
        source = DataSource.objects.create(
            nom='NOAA NCEI — GHCN-Daily', slug='noaa-ghcn',
            url='https://www.ncei.noaa.gov', license_nom='Domaine public',
        )
        station_data = ghcn.parse_stations(INVENTAIRE_FIXTURE)[0]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"{station_data['station_id']}.csv"
            ecrire_csv_ghcn(path, [
                *jours_janvier_2020(),
                {'date': '2021-08-01', 'PRCP': '1500', 'TAVG': '290',
                 'TMIN': '260', 'TMAX': '330'},
                {'date': '2021-09-01', 'PRCP': '100', 'TAVG': '285'},
            ])
            agrege = ghcn.agreer_mensuel(ghcn.parser_journalier(path))
        ghcn.importer_station(station_data, agrege, source=source)

    def api_get(self, url, query=''):
        response = self.client.get(url + query)
        self.assertEqual(response.status_code, 200, url + query)
        return response.json()

    def test_liste_stations_avec_nb_observations(self):
        data = self.api_get(self.URL_STATIONS)
        self.assertEqual(data['count'], 1)
        station = data['results'][0]
        self.assertEqual(station['station_id'], STATION_YOFF)
        self.assertEqual(station['nb_observations'], 3)

    def test_detail_station_par_station_id(self):
        response = self.client.get(self.URL_STATIONS + STATION_YOFF + '/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['nom'], 'Dakar/Yoff')

    def test_recherche_stations_par_nom(self):
        data = self.api_get(self.URL_STATIONS, '?search=yoff')
        self.assertEqual(data['count'], 1)
        data = self.api_get(self.URL_STATIONS, '?search=SGM')
        self.assertEqual(data['count'], 0)

    def test_observations_filtre_station_et_ordering_prcp(self):
        data = self.api_get(
            self.URL_OBSERVATIONS,
            f'?station={STATION_YOFF}&ordering=-prcp_mm',
        )
        self.assertEqual(data['count'], 3)
        precipitations = [row['prcp_mm'] for row in data['results']]
        self.assertEqual(precipitations, ['150.00', '12.00', '10.00'])

    def test_observations_filtres_annee_min_max(self):
        data = self.api_get(
            self.URL_OBSERVATIONS,
            f'?station={STATION_YOFF}&annee_min=2021&ordering=annee',
        )
        self.assertEqual(data['count'], 2)
        data = self.api_get(
            self.URL_OBSERVATIONS,
            f'?station={STATION_YOFF}&annee_min=2020&annee_max=2020',
        )
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['mois'], 1)

    def test_observations_filtre_mois(self):
        data = self.api_get(
            self.URL_OBSERVATIONS,
            f'?station={STATION_YOFF}&mois=8&ordering=-annee',
        )
        self.assertEqual(data['count'], 1)
        resultat = data['results'][0]
        self.assertEqual(resultat['annee'], 2021)
        self.assertAlmostEqual(float(resultat['tavg']), 29.0)
        self.assertEqual(resultat['station_nom'], 'Dakar/Yoff')

    def test_pagination_page_size(self):
        data = self.api_get(self.URL_OBSERVATIONS, '?page_size=2&page=1')
        self.assertEqual(len(data['results']), 2)
