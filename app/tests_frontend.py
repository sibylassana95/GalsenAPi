"""Tests des pages frontend (Phase 7)."""
from django.test import TestCase


class PagesFrontendTests(TestCase):
    """Les pages doivent répondre 200 même sur une base vide."""

    def test_accueil(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'GalsenAPI')

    def test_explorateur(self):
        r = self.client.get('/donnees/')
        self.assertEqual(r.status_code, 200)

    def test_explorateur_filtre_categorie(self):
        r = self.client.get('/donnees/', {'categorie': 'climat', 'q': 'climat'})
        self.assertEqual(r.status_code, 200)

    def test_regions_liste(self):
        r = self.client.get('/region/')
        self.assertEqual(r.status_code, 200)

    def test_region_detail_404(self):
        r = self.client.get('/regions/SNZZ/')
        self.assertEqual(r.status_code, 404)

    def test_departement_detail_404(self):
        r = self.client.get('/departements/SNZZ01/')
        self.assertEqual(r.status_code, 404)

    def test_dashboard_demographie(self):
        r = self.client.get('/demographie/')
        self.assertEqual(r.status_code, 200)

    def test_dashboard_agriculture(self):
        r = self.client.get('/agriculture/')
        self.assertEqual(r.status_code, 200)

    def test_dashboard_climat(self):
        r = self.client.get('/climat/')
        self.assertEqual(r.status_code, 200)

    def test_dashboard_economie(self):
        r = self.client.get('/economie/')
        self.assertEqual(r.status_code, 200)

    def test_education(self):
        r = self.client.get('/education/', {'q': 'univers'})
        self.assertEqual(r.status_code, 200)

    def test_developers(self):
        r = self.client.get('/developers/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '/api/v1/')
