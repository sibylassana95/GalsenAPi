# GalsenAPI 2.0

<div align="center">
  <img src="static/images/logo-galsenapi.png" alt="GalsenAPI" width="220" />
  <p><strong>La plateforme ouverte pour explorer les données du Sénégal.</strong></p>
  <p>
    <a href="./Licence.md"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="Licence MIT" /></a>
    <img src="https://img.shields.io/badge/django-5.2-44B78B" alt="Django 5.2" />
    <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1" alt="PostgreSQL" />
    <img src="https://img.shields.io/badge/tests-144%20OK-brightgreen" alt="Tests" />
  </p>
  <p>
    <a href="https://galsenapi.lassanasiby.com/">Démonstration</a>
    <span> · </span>
    <a href="https://galsenapi.lassanasiby.com/docs/">Documentation API (Swagger)</a>
    <span> · </span>
    <a href="https://github.com/sibylassana95/GalsenAPi">GitHub</a>
  </p>
</div>

---

## Qu'est-ce que GalsenAPI ?

GalsenAPI est une plateforme **open source** dédiée aux données publiques du Sénégal.
Elle permet de découvrir, comprendre, explorer, comparer et télécharger des données
officielles sourcées — géographie, démographie, agriculture, économie, climat,
éducation — via une interface web moderne et une **API REST documentée**.

> Une donnée inconnue reste inconnue : aucune valeur n'est inventée. Chaque chiffre
> est tracé vers sa source (ANSD, FAO, Banque mondiale, NOAA, HDX…) avec sa licence.

## Contenu des données

| Domaine | Source (licence) | Volume |
|---|---|---|
| Géographie | HDX COD-AB (CC BY-IGO) + Galsenify (MIT) | 14 régions · 46 départements · 125 arrondissements · 8 635 villages · géométries GeoJSON |
| Démographie | ANSD — RGPH-5 2023 (CC BY 4.0) | 18 126 388 habitants, par région et département, hommes/femmes |
| Agriculture | FAOSTAT (CC BY 4.0) | 105 cultures · 11 694 observations · 1961-2024 |
| Économie | Banque mondiale (CC BY 4.0) | 21 indicateurs · 943 observations · 1960-2025 |
| Climat | NOAA GHCN-Daily (domaine public) | 14 stations · 9 027 mois-station · 1950-2025 |
| Éducation | Galsenify (MIT) | 86 établissements d'enseignement supérieur |

## API v1

Base : `https://galsenapi.lassanasiby.com/api/v1/` — pagination (50/page, `?page_size=` jusqu'à 200),
recherche (`?search=`), filtres, tri (`?ordering=`), limite 60 req/min par IP.

| Endpoint | Description |
|---|---|
| `regions` · `departements` · `arrondissements` · `communes` · `villages` · `pays` | Hiérarchie administrative (P-codes stables) |
| `regions/geojson/` | Frontières complètes (FeatureCollection, cache 30 min) |
| `regions/{pcode}/geometry/` | Géométrie d'une entité (léger) |
| `search/?q=` | Recherche multi-entités (`?types=`, `?limit=`) |
| `statistics/` · `statistics/regions/{pcode}/` | Agrégats calculés depuis les données réelles |
| `demographie/population/` | RGPH-5 2023 (`?niveau=`, `?region=`, `?annee=`) |
| `agriculture/cultures/` · `agriculture/production/` | FAOSTAT (`?element=`, `?annee_min=`…) |
| `economie/indicateurs/` · `economie/observations/` | Banque mondiale (`?indicateur=CODE`) |
| `climat/stations/` · `climat/observations/` | NOAA GHCN (`?station=`, `?annee_min=`) |
| `datasets/` · `datasets/{slug}/download/?format=json\|csv\|geojson` | Catalogue sourcé + exports |

Les anciennes routes `/api/<entité>/` restent servies pour compatibilité (dépréciation progressive).

### Exemples

**curl**
```bash
curl "https://galsenapi.lassanasiby.com/api/v1/search/?q=kanel"
```

**Python**
```python
import requests

r = requests.get(
    "https://galsenapi.lassanasiby.com/api/v1/departements/",
    params={"region": "SN01", "ordering": "-population"},
)
for dept in r.json()["results"]:
    print(dept["nom"], dept["population"])
```

**JavaScript**
```js
const r = await fetch("https://galsenapi.lassanasiby.com/api/v1/statistics/");
const stats = await r.json();
console.log(stats.population.totale); // 18126388 (RGPH-5 2023)
```

**Java**
```java
var http = java.net.http.HttpClient.newHttpClient();
var req = java.net.http.HttpRequest.newBuilder()
        .uri(java.net.URI.create("https://galsenapi.lassanasiby.com/api/v1/regions/?ordering=-population"))
        .build();
var reponse = http.send(req, java.net.http.HttpResponse.BodyHandlers.ofString());
System.out.println(reponse.body());
```

## Architecture

```
GalsenAPi/
├── GalsenifyDj/          # settings (base/local/production), urls, vues frontend, filtres
├── app/                  # modèles legacy (compat) + tests pages frontend
├── geo/                  # hiérarchie administrative + ingestion HDX + API + recherche + stats
├── datasets/             # DataSource → Dataset → DatasetVersion → DataQualityReport + exports
├── demographie/          # RGPH-5 2023 (ANSD)
├── agriculture/          # FAOSTAT
├── economie/             # Banque mondiale
├── climat/               # NOAA GHCN
├── templates/            # design system « Institutional Modern » (Tailwind compilé)
├── static/               # css compilé, js, images
├── dataset/              # JSON legacy d'origine
└── var/                  # caches d'ingestion + rapports (non versionnés)
```

Chaque domaine suit le même schéma : `models.py`, `api/` (viewsets DRF),
`management/commands/import_<domaine>.py` (pipeline téléchargement → parse → validation
→ upsert idempotent), provenance dans `meta` et catalogue `datasets`.

## Installation

Prérequis : Python 3.12+, PostgreSQL 14+ (ou SQLite pour essayer).

```bash
git clone https://github.com/sibylassana95/GalsenAPi.git
cd GalsenAPi
python -m venv venv
venv\Scripts\activate            # Windows  (Linux/macOS : source venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env             # puis renseigner SECRET_KEY, POSTGRES_*…
python manage.py migrate
python manage.py createsuperuser
```

### Chargement des données (reproductible, caches locaux)

```bash
python manage.py import_geo            # limites HDX + legacy (villages, communes)
python manage.py sync_datasets         # catalogue des sources/datasets
python manage.py import_demographie    # RGPH-5 2023 (data/rgph5_2023.json)
python manage.py import_agriculture    # FAOSTAT (zip ~34 Mo)
python manage.py import_economie       # Banque mondiale (API)
python manage.py import_climat         # NOAA GHCN (14 stations)
```

Chaque commande est **idempotente** (relançable sans doublons) et accepte `--offline`
pour n'utiliser que le cache `var/ingest/`. Les rapports qualité sont écrits dans `var/reports/`.

### Développement frontend

```powershell
.\build_css.ps1     # compile Tailwind (tools/tailwindcss.exe) → static/css/galsenapi.css
```

À exécuter après toute nouvelle classe utilitaire dans un template.

### Docker

```bash
docker compose up
```

Lance Django + PostgreSQL 16. Variables via `.env` (voir `.env.example`).

## Tests

```bash
python manage.py test
```

144 tests : modèles, hiérarchie, ingestion, API (pagination, filtres, tri, GeoJSON),
recherche, statistiques, exports, pages frontend.

## Déploiement

Hébergé sur cPanel (`galsenapi.lassanasiby.com`) : Python 3.12 via `build_files.sh`,
PostgreSQL, WhiteNoise pour les statiques. Définir en production :
`DJANGO_ENV=production`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `POSTGRES_*`.

## Sources et licences des données

| Source | Licence | Redistribution |
|---|---|---|
| [HDX COD-AB Sénégal](https://data.humdata.org/dataset/cod-ab-sen) | CC BY-IGO | Oui |
| [ANSD (RGPH-5 2023)](https://www.ansd.sn/) | CC BY 4.0 (revendiquée côté anads.ansd.sn) | Oui |
| [FAOSTAT](https://www.fao.org/faostat/) | CC BY 4.0 | Oui |
| [Banque mondiale](https://data.worldbank.org/) | CC BY 4.0 | Oui |
| [NOAA GHCN-Daily](https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily) | Domaine public | Oui |
| [Galsenify](https://github.com/GalsenDev221/galsenify) | MIT | Oui |

Les données dont la licence interdit la redistribution ne sont pas copiées :
seules leurs métadonnées et un lien vers la source sont référencés.

## Contribution

Les contributions sont bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md).
Signaler une donnée incorrecte ou manquante : ouvrez une issue avec le modèle
« Data correction » ou « Dataset request ».

## Roadmap

- [x] Phase 1-7 : modernisation, modèle géo, API v1, datasets, recherche/stats, domaines, frontend
- [ ] Phase 10 : CI/CD GitHub Actions + pytest + audits sécurité
- [ ] Phase 11 : serveur MCP (GalsenAPI MCP pour assistants IA)
- [ ] Source officielle des ~557 communes (rattachement complet aux départements)
- [ ] Domaines supplémentaires selon disponibilité de sources ouvertes (santé, transport, énergie)

## Licence

[Licence.md](Licence.md) — MIT avec attribution de l'auteur original
[Lassana Siby](https://github.com/sibylassana95).
