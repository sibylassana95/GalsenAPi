import csv
import io
import tempfile
import zipfile
from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase

from agriculture.faostat import (
    BULK_URL,
    importer_lignes,
    lignes_normalisees,
    membre_donnees,
)
from agriculture.models import Culture, ProductionAgricole
from datasets.models import DataSource

HEADER = [
    'Area Code', 'Area Code (M49)', 'Area', 'Item Code', 'Item Code (CPC)',
    'Item', 'Element Code', 'Element', 'Year Code', 'Year', 'Unit',
    'Value', 'Flag', 'Note',
]


def _ligne(area_code, m49, area, code, cpc, nom, elem_code, elem,
           annee, unit, valeur, flag=''):
    return [area_code, m49, area, code, cpc, nom, elem_code, elem,
            annee, annee, unit, valeur, flag, '']


def csv_mini_faostat():
    """Mini extrat FAOSTAT QCL normalisé : Sénégal + Mali, éléments réels."""
    lignes = [
        _ligne('195', "'686", 'Senegal', '236', "'00236",
               'Groundnuts, excluding shelled', '5510', 'Production',
               '2022', 't', '1700000.000000', 'Fc'),
        _ligne('195', "'686", 'Senegal', '236', "'00236",
               'Groundnuts, excluding shelled', '5312', 'Area harvested',
               '2022', 'ha', '1200000.000000', 'Fc'),
        _ligne('195', "'686", 'Senegal', '236', "'00236",
               'Groundnuts, excluding shelled', '5412', 'Yield',
               '2022', 'kg/ha', '1416.66666667', 'Fc'),
        _ligne('195', "'686", 'Senegal', '27', "'00127", 'Rice',
               '5510', 'Production', '1961', 't', '120000.000000', 'A'),
        _ligne('195', "'686", 'Senegal', '27', "'00127", 'Rice',
               '5412', 'Yield', '1961', 'kg/ha', '', 'A'),
        _ligne('195', "'686", 'Senegal', '27', "'00127", 'Rice',
               '5412', 'Yield', '2022', 'kg/ha', 'No numeric', 'Fc'),
        _ligne('195', "'686", 'Senegal', '1058', "'01058",
               'Meat of chickens, fresh or chilled', '5510', 'Production',
               '2022', 't', '60000.000000', 'Fc'),
        # Production d'œufs en '1000 No' : unité non retenue -> ignoré.
        _ligne('195', "'686", 'Senegal', '1062', "'01062",
               'Hen eggs in shell, fresh', '5510', 'Production',
               '2022', '1000 No', '900.000000', 'Fc'),
        # Stocks d'animaux : élément non retenu -> ignoré.
        _ligne('195', "'686", 'Senegal', '1107', "'01107", 'Asses',
               '5111', 'Stocks', '1961', 'An', '65000.000000'),
        # Autre pays -> ignoré.
        _ligne('146', "'466", 'Mali', '236', "'00236",
               'Groundnuts, excluding shelled', '5510', 'Production',
               '2022', 't', '999.000000', 'Fc'),
    ]
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(HEADER)
    writer.writerows(lignes)
    return buffer.getvalue().encode('latin-1')


def ecrire_zip_mini(tmp_path):
    zip_path = Path(tmp_path) / 'mini_qcl.zip'
    with zipfile.ZipFile(zip_path, 'w') as archive:
        archive.writestr(
            'Production_Crops_Livestock_E_All_Data_(Normalized).csv',
            csv_mini_faostat(),
        )
    return zip_path


class PipelineAgricultureTests(TestCase):
    def run_import(self, **kwargs):
        meta_base = {'bulk_dataset': BULK_URL, 'downloaded_at': '2026-01-01T00:00:00+00:00'}
        source, _ = DataSource.objects.update_or_create(
            slug='faostat',
            defaults={
                'nom': 'FAO — FAOSTAT',
                'url': 'https://www.fao.org/faostat/en/#data/QCL',
                'license_nom': 'CC BY 4.0',
            },
        )
        return importer_lignes(
            (l for l in lignes_normalisees(io.BytesIO(csv_mini_faostat()))
             if l['area'] == 'Senegal'),
            source=source, meta_base=meta_base, **kwargs,
        )

    def test_membre_donnees_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = ecrire_zip_mini(tmp)
            self.assertEqual(
                membre_donnees(zip_path),
                'Production_Crops_Livestock_E_All_Data_(Normalized).csv',
            )

    def test_import_mapping_elements_et_valeurs(self):
        stats = self.run_import()

        self.assertEqual(Culture.objects.count(), 3)
        self.assertEqual(stats['compteurs'], {
            'production_tonnes': 3,
            'superficie_recoltee_ha': 1,
            'rendement_hg_ha': 3,
        })
        self.assertEqual(stats['an_min'], 1961)
        self.assertEqual(stats['an_max'], 2022)

        arachide = Culture.objects.get(code_faostat='236')
        self.assertEqual(arachide.nom, 'Groundnuts, excluding shelled')

        production = ProductionAgricole.objects.get(
            culture=arachide, annee=2022, element='production_tonnes'
        )
        self.assertEqual(str(production.valeur), '1700000.0000')
        self.assertEqual(production.flag, 'Fc')
        self.assertEqual(production.meta['bulk_dataset'], BULK_URL)
        self.assertEqual(production.source.slug, 'faostat')

        superficie = ProductionAgricole.objects.get(
            culture=arachide, annee=2022, element='superficie_recoltee_ha'
        )
        self.assertEqual(str(superficie.valeur), '1200000.0000')

        # Rendement kg/ha converti x10 en hg/ha, conversion tracée dans meta.
        rendement = ProductionAgricole.objects.get(
            culture=arachide, annee=2022, element='rendement_hg_ha'
        )
        self.assertEqual(str(rendement.valeur), '14166.6667')
        self.assertEqual(rendement.meta['unite_source'], 'kg/ha')
        self.assertEqual(rendement.meta['conversion'], 'x10 vers hg/ha')

        # Viande de volaille (produit élevage QCL) bien conservée.
        self.assertTrue(
            ProductionAgricole.objects.filter(
                culture__code_faostat='1058', element='production_tonnes'
            ).exists()
        )
        # Éléments/unités hors périmètre et autres pays exclus.
        self.assertFalse(Culture.objects.filter(code_faostat='1062').exists())
        self.assertFalse(Culture.objects.filter(code_faostat='1107').exists())
        self.assertEqual(ProductionAgricole.objects.count(), 7)

    def test_valeurs_non_numeriques_deviennent_null(self):
        self.run_import()
        riz = Culture.objects.get(code_faostat='27')
        rendements = ProductionAgricole.objects.filter(
            culture=riz, element='rendement_hg_ha'
        ).order_by('annee')
        self.assertEqual(rendements.count(), 2)
        for rendement in rendements:
            self.assertIsNone(rendement.valeur)

    def test_import_idempotent(self):
        self.run_import()
        arachide = Culture.objects.get(code_faostat='236')
        production = ProductionAgricole.objects.get(
            culture=arachide, annee=2022, element='production_tonnes'
        )
        production.valeur = Decimal('1.0000')
        production.save(update_fields=['valeur'])

        stats = self.run_import()

        self.assertEqual(Culture.objects.count(), 3)
        self.assertEqual(ProductionAgricole.objects.count(), 7)
        self.assertEqual(stats['crees'], 0)
        production.refresh_from_db()
        self.assertEqual(str(production.valeur), '1700000.0000')

    def test_years_from_limite_la_plage(self):
        stats = self.run_import(years_from=2000)
        self.assertEqual(stats['an_min'], 2022)
        riz = Culture.objects.get(code_faostat='27')
        self.assertFalse(
            ProductionAgricole.objects.filter(culture=riz, annee=1961).exists()
        )
        self.assertEqual(ProductionAgricole.objects.count(), 5)

    def test_contrainte_unicite_culture_annee_element(self):
        self.run_import()
        arachide = Culture.objects.get(code_faostat='236')
        with self.assertRaises(IntegrityError):
            ProductionAgricole.objects.create(
                culture=arachide, annee=2022, element='production_tonnes',
                valeur=Decimal('42'),
            )


class CommandeImportAgricultureTests(TestCase):
    def test_commande_complete_sans_telechargement(self):
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = ecrire_zip_mini(tmp)
            out = StringIO()
            call_command('import_agriculture', fichier=str(zip_path),
                         stdout=out)
            sortie = out.getvalue()

            self.assertIn('Top 5 cultures 2022', sortie)
            self.assertIn('Groundnuts, excluding shelled', sortie)

            # Deuxième exécution : idempotence au niveau commande.
            call_command('import_agriculture', fichier=str(zip_path))

        self.assertTrue(DataSource.objects.filter(slug='faostat').exists())
        self.assertEqual(Culture.objects.count(), 3)
        self.assertEqual(ProductionAgricole.objects.count(), 7)


class AgricultureApiTests(TestCase):
    URL_PRODUCTION = '/api/v1/agriculture/production/'
    URL_CULTURES = '/api/v1/agriculture/cultures/'

    @classmethod
    def setUpTestData(cls):
        meta_base = {'bulk_dataset': BULK_URL, 'downloaded_at': 'x'}
        source = DataSource.objects.create(
            nom='FAO — FAOSTAT', slug='faostat',
            url='https://www.fao.org/faostat/en/#data/QCL',
            license_nom='CC BY 4.0',
        )
        importer_lignes(
            (l for l in lignes_normalisees(io.BytesIO(csv_mini_faostat()))
             if l['area'] == 'Senegal'),
            source=source, meta_base=meta_base,
        )

    def api_get(self, url, query=''):
        response = self.client.get(url + query)
        self.assertEqual(response.status_code, 200, url + query)
        return response.json()

    def test_liste_cultures(self):
        data = self.api_get(self.URL_CULTURES)
        self.assertEqual(data['count'], 3)
        codes = {row['code_faostat'] for row in data['results']}
        self.assertEqual(codes, {'236', '27', '1058'})

    def test_recherche_cultures_par_nom(self):
        data = self.api_get(self.URL_CULTURES, '?search=chickens')
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['nom'],
                         'Meat of chickens, fresh or chilled')

    def test_production_filtre_culture_et_element(self):
        data = self.api_get(self.URL_PRODUCTION,
                            '?culture=236&element=production_tonnes')
        self.assertEqual(data['count'], 1)
        ligne = data['results'][0]
        self.assertEqual(ligne['culture_nom'],
                         'Groundnuts, excluding shelled')
        self.assertEqual(ligne['element_display'], 'Production (tonnes)')
        self.assertEqual(ligne['annee'], 2022)
        self.assertEqual(ligne['flag'], 'Fc')

    def test_production_filtres_annees(self):
        data = self.api_get(self.URL_PRODUCTION, '?annee_min=2022')
        self.assertEqual(data['count'], 5)
        data = self.api_get(self.URL_PRODUCTION,
                            '?annee_min=1900&annee_max=1961')
        self.assertEqual(data['count'], 2)
        annees = {row['annee'] for row in data['results']}
        self.assertEqual(annees, {1961})

    def test_production_recherche_nom_culture(self):
        data = self.api_get(self.URL_PRODUCTION, '?search=Rice')
        self.assertEqual(data['count'], 3)
        for row in data['results']:
            self.assertEqual(row['culture'], Culture.objects.get(nom='Rice').id)

    def test_production_ordering_valeur(self):
        data = self.api_get(self.URL_PRODUCTION,
                            '?element=production_tonnes&ordering=-valeur')
        valeurs = [row['valeur'] for row in data['results']]
        self.assertEqual(valeurs, sorted(valeurs, key=lambda v: float(v),
                                         reverse=True))

    def test_production_ordering_annee(self):
        data = self.api_get(self.URL_PRODUCTION, '?culture=27&ordering=annee')
        annees = [row['annee'] for row in data['results']]
        self.assertEqual(annees, sorted(annees))

    def test_element_invalide_400(self):
        response = self.client.get(self.URL_PRODUCTION + '?element=bushels')
        self.assertEqual(response.status_code, 400)

    def test_pagination_page_size(self):
        data = self.api_get(self.URL_PRODUCTION, '?page_size=2&page=2')
        self.assertEqual(data['count'], 7)
        self.assertLessEqual(len(data['results']), 2)
