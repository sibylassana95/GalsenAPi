# GalsenAPI MCP

Serveur MCP (Model Context Protocol) exposant les données du Sénégal aux
assistants IA : géographie, démographie (RGPH-5), agriculture (FAOSTAT),
économie (Banque mondiale), climat (NOAA) et catalogue de datasets.

**Principe** : l'assistant ne devine rien — chaque réponse provient de l'API
GalsenAPI. Si une donnée n'existe pas, l'outil le dit.

## Installation

```bash
cd mcp-server
python -m venv venv && venv\Scripts\activate   # ou source venv/bin/activate
pip install -r requirements.txt
```

## Lancement manuel (stdio)

```bash
set GALSENAPI_BASE_URL=https://galsenapi.lassanasiby.com   # optionnel
python server.py
```

## Configuration Claude Desktop

`claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "galsenapi": {
      "command": "python",
      "args": ["C:/chemin/vers/GalsenAPi/mcp-server/server.py"],
      "env": { "GALSENAPI_BASE_URL": "https://galsenapi.lassanasiby.com" }
    }
  }
}
```

## Configuration opencode

`opencode.json` :

```json
{
  "mcp": {
    "galsenapi": {
      "type": "local",
      "command": ["python", "C:/chemin/vers/GalsenAPi/mcp-server/server.py"],
      "environment": { "GALSENAPI_BASE_URL": "https://galsenapi.lassanasiby.com" }
    }
  }
}
```

## Outils exposés

| Outil | Description |
|---|---|
| `rechercher(q, types?, limite?)` | Recherche globale multi-entités |
| `lister_regions()` | Les 14 régions (P-code, population RGPH-5, superficie) |
| `obtenir_region(pcode)` | Détail d'une région + départements |
| `lister_entites(niveau, region_pcode?, departement_pcode?, q?, page_size?)` | Départements / arrondissements / communes / villages filtrés |
| `statistiques_nationales()` | Agrégats nationaux |
| `statistiques_region(pcode)` | Statistiques détaillées d'une région |
| `production_agricole(element?, culture?, annee_min?, annee_max?…)` | FAOSTAT 1961-2024 |
| `indicateurs_economiques(code?, annee_min?)` | Banque mondiale (PIB, inflation, croissance…) |
| `stations_climatiques()` | Les 14 stations GHCN |
| `observations_climatiques(station?, annee_min?, annee_max?…)` | Températures et pluies mensuelles |
| `demographie(annee?, niveau?)` | Population RGPH-5 par région/département |
| `jeux_de_donnees()` | Catalogue sourcé + licences |

## Exemples de questions

- « Quelles sont les communes rattachées au département de Kanel ? »
- « Quelle est la population de la région de Matam selon le RGPH-5 ? »
- « Top 5 des productions agricoles en 2024 »
- « Évolution du PIB du Sénégal depuis 2000 »
- « Précipitations à la station de Podor en 2023 »

## Tests

```bash
pytest test_server.py -q
```

Transport HTTP simulé — aucun appel réseau pendant les tests.
