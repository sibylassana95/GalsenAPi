# Changelog

Tous les changements notables de GalsenAPI sont documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/)
et le versionnage suit [SemVer](https://semver.org/lang/fr/).

## [2.0.0] — 2026-08-23

Modernisation complète de la plateforme : API v1, données officielles sourcées,
nouveau frontend, PostgreSQL.

### Ajouté

#### Socle technique
- Settings modulaires `GalsenifyDj/settings/` (base/local/production) pilotés par `DJANGO_ENV` et `.env`
  (`override=True` : le `.env` est la source de vérité) — commits `82228d4`, `7fc76a5`, `c3fe4c2`
- PostgreSQL via psycopg 3 (`DB_ENGINE=postgresql`), Docker Compose (Django + postgres:16-alpine), `.env.example`
- Pagination DRF globale (50/page, `?page_size=` jusqu'à 200) et throttling anonyme 60 req/min
- Filtre d'ordre `NullsLastOrderingFilter` appliqué à toute l'API (sémantique identique SQLite/PostgreSQL)

#### Modèle géographique (`geo`)
- Hiérarchie FK `Pays → Region → Departement → Arrondissement → Commune → Village`
  avec P-codes HDX uniques, géométries GeoJSON (JSONField), centroïdes lat/lng (`8dd5652`)
- Ingestion reproductible `import_geo` (HDX COD-AB, cache `var/ingest/codab/`, rapports `var/reports/`)

#### API v1 (`/api/v1/`)
- Viewsets paginés/filtrés/triables pour les 6 niveaux administratifs (`356c857`)
- Exports GeoJSON : `regions/geojson/` (cache 30 min) et géométries unitaires
  `regions|departements/{pcode}/geometry/` (`7e7e02f`)
- Recherche globale multi-entités `search/?q=` typée avec parent et URL (`31bc969`)
- Statistiques `statistics/` et `statistics/regions/{pcode}/` (agrégats ORM, cache 10 min)
- Documentation Swagger/ReDoc régénérée, **filtrée sur `/api/v1/`** (les routes legacy restent servies hors doc)
- Compatibilité : les anciennes routes `/api/<entité>/` répondent toujours

#### Système de datasets et provenance (`datasets`)
- `DataSource → Dataset → DatasetVersion → DataQualityReport`, catalogue factuel
  6 sources / 9 datasets, commande `sync_datasets` idempotente (`9f87fa2`)
- Exports `datasets/{slug}/download/?format=json|csv|geojson` (CSV BOM UTF-8, GeoJSON `application/geo+json`)

#### Domaines de données
- **Démographie** — RGPH-5 2023 officiel (ANSD) : 14 régions (hommes/femmes) + 46 départements,
  total 18 126 388 (écart −2 vs total national documenté) ; remplace les chiffres legacy
  ; endpoint `demographie/population/` (`c1930be`)
- **Agriculture** — FAOSTAT : 105 cultures, 11 694 records (production/superficie/rendement), 1961-2024 (`7b9f4e1`)
- **Économie** — Banque mondiale : 21 indicateurs, 943 observations, 1960-2025 (`c59b143`)
- **Climat** — NOAA GHCN-Daily : 14 stations sénégalaises, 9 027 mois-station, 1950-2025 (`518292b`)

#### Frontend (Django Templates, design system « Institutional Modern »)
- Tailwind **compilé localement** (fini le CDN), tokens du design system, dark mode sans reload (`a9a00fc`)
- Recherche globale instantanée (autocomplete clavier/ARIA) branchée sur `/api/v1/search/`
- Homepage : chiffres clés animés, **carte chorophlète réelle** (géométries HDX, Leaflet 1.9.4),
  catégories vers pages dédiées (`9b5e8eb`, `d987c2f`)
- Explorateur `/donnees/` par domaine + explorateur géographique paginé
  `/donnees/geographie/` (onglets, recherche, 25/page) (`7eb5166`)
- Pages territoriales région/département avec carte Leaflet et vraies frontières (`7e7e02f`)
- Dashboards Démographie / Agriculture / Climat / Économie (Chart.js 4.4.1, données serveur) (`a78e676`)
- Pages Éducation (86 établissements) et Développeurs ; pages d'erreur unifiées
- Logo : variante blanche automatique en mode sombre, tailles inline robustes (`3b2db45`)

### Corrigé
- Suppression de la synchro HTTP vers GitHub à chaque requête (anti-pattern de latence)
- `django-rest-swagger` (abandonné) retiré ; DRF 3.16 compatible Django 5.2
- `django_filters` manquant à `INSTALLED_APPS` → erreur de template sur l'API HTML navigable
- Collision `ref_name` des sérialiseurs `Pays` (legacy vs v1) → `/docs?format=openapi` 500
- Coordonnées localisées fr (virgules) cassant Leaflet → filtre `|unlocalize`
- Encodage : fichiers dataset validés UTF-8 ; doublons du JSON universités dédupliqués (95 → 86)
- Repo nettoyé : 644 statiques collectés dé-commités, `data.json` (fixture) supprimé

### Sécurité
- `ALLOWED_HOSTS` et `CORS_ALLOWED_ORIGINS` explicites (fini `*`), secrets hors dépôt via `.env`
- `.env.example` documenté ; `.env` jamais lu ni commité

### Compatibilité / migration
- Base : nouvelles migrations par app ; charger les données avec les commandes `import_*`
  (toutes idempotentes, `--offline` possible via caches)
- API : aucun breaking change sur les anciennes routes `/api/*` ; l'API moderne vit sous `/api/v1/`

## [1.x] — 2023-2025

Version historique : API non versionnée sur données JSON statiques (régions, départements,
villages, universités), frontend Django Templates + Tailwind CDN, déploiement Vercel/cPanel.
Voir l'historique Git.
