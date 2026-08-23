"""Tests de l'import des communes officielles (Répertoire des localités ANSD)."""

import csv
import io
from pathlib import Path
from unittest import mock

from django.test import TestCase

from geo import ansd
from geo.models import Commune, Departement, Pays, Region
from geo.management.commands.import_communes import Command


def csv_mini_ansd():
    lignes = [
        ["Region", "Departement", "COM_ARRT_VILLE", "COMMUNE",
         "QUARTIER_VILLAGE_HAMEAU", "CONCESSION", "MENAGE", "HOMMES", "FEMMES",
         "POPULATION"],
        ["MATAM", "MATAM", "VILLE DE MATAM", "MATAM", "QUARTIER 1", "10", "20",
         "1000", "1100", "2100"],
        ["MATAM", "MATAM", "VILLE DE MATAM", "MATAM", "QUARTIER 2", "5", "8",
         "400", "500", "900"],
        ["MATAM", "KANEL", "KANEL", "KANEL", "QUARTIER 1", "7", "9",
         "600", "650", "1250"],
        ["MATAM", "OROLOGUI", "OROLOGUI", "INCONNUE", "VILLAGE X", "1", "1",
         "10", "10", "20"],
    ]
    tampon = io.StringIO()
    writer = csv.writer(tampon)
    writer.writerows(lignes)
    return tampon.getvalue()


class ImportCommunesTests(TestCase):
    def setUp(self):
        pays = Pays.objects.create(nom="Sénégal", code_iso2="SN")
        self.region_matam = Region.objects.create(pays=pays, pcode="SN09", nom="Matam")
        self.dept_matam = Departement.objects.create(
            region=self.region_matam, pcode="SN0901", nom="Matam"
        )
        self.dept_kanel = Departement.objects.create(
            region=self.region_matam, pcode="SN0902", nom="Kanel"
        )
        # Commune legacy déjà rattachée (doit être mise à jour, pas dupliquée)
        Commune.objects.create(
            departement=self.dept_kanel, nom="Kanel", population=None
        )

    def _lancer_import(self):
        with mock.patch.object(
            ansd, "telecharger", return_value=Path("cache-inutile.csv")
        ), mock.patch(
            "geo.ansd.open",
            mock.mock_open(read_data=csv_mini_ansd()),
        ):
            commande = Command()
            commande.stdout = type("Sortie", (), {"write": staticmethod(lambda s: None)})()
            commande.style = type("Style", (), {"SUCCESS": staticmethod(lambda s: s)})()
            commande.handle(offline=True, timeout=1)

    def test_rattachement_et_population(self):
        self._lancer_import()
        commune_matam = Commune.objects.get(departement=self.dept_matam)
        self.assertEqual(commune_matam.nom, "MATAM")
        self.assertEqual(commune_matam.population, 3000)  # 2100 + 900
        self.assertEqual(
            commune_matam.meta["population_source"],
            "RGPH-5 2023 (ANSD, Répertoire des localités)",
        )

    def test_mise_a_jour_sans_duplication(self):
        self._lancer_import()
        kanel = Commune.objects.filter(departement=self.dept_kanel)
        self.assertEqual(kanel.count(), 1)
        self.assertEqual(kanel.first().population, 1250)

    def test_departement_inconnu_ignore(self):
        self._lancer_import()
        self.assertFalse(
            Commune.objects.filter(nom__iexact="INCONNUE").exists()
        )

    def test_idempotent(self):
        self._lancer_import()
        total = Commune.objects.count()
        self._lancer_import()
        self.assertEqual(Commune.objects.count(), total)
