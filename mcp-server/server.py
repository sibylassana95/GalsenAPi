"""Serveur MCP GalsenAPI.

Expose les données du Sénégal (géographie, démographie, agriculture,
économie, climat, datasets) aux assistants IA via le protocole MCP.

Toutes les réponses proviennent de l'API GalsenAPI — le modèle ne doit
jamais inventer une valeur : en cas de doute, appeler un outil.

Configuration :
    GALSENAPI_BASE_URL  URL de base de l'API (défaut http://127.0.0.1:8000)
    GALSENAPI_TIMEOUT   timeout HTTP en secondes (défaut 30)

Lancement (stdio) :
    python server.py
"""

import json
import os
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = os.environ.get("GALSENAPI_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = float(os.environ.get("GALSENAPI_TIMEOUT", "30"))

mcp = FastMCP("GalsenAPI")

# Transport injectable pour les tests (httpx.MockTransport)
_transport: Optional[httpx.AsyncBaseTransport] = None


def _client() -> httpx.AsyncClient:
    if _transport is not None:
        return httpx.AsyncClient(base_url=BASE_URL, transport=_transport, timeout=TIMEOUT)
    return httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT)


async def _get(chemin: str, params: Optional[dict] = None) -> str:
    params = {k: v for k, v in (params or {}).items() if v not in (None, "", [])}
    try:
        async with _client() as client:
            reponse = await client.get(chemin, params=params)
            reponse.raise_for_status()
            return json.dumps(reponse.json(), ensure_ascii=False, indent=2)
    except httpx.HTTPStatusError as erreur:
        detail = ""
        try:
            detail = erreur.response.json().get("detail", "")
        except Exception:
            detail = erreur.response.text[:200]
        return json.dumps(
            {"erreur": f"HTTP {erreur.response.status_code}", "details": detail},
            ensure_ascii=False,
        )
    except httpx.HTTPError as erreur:
        return json.dumps(
            {"erreur": "API injoignable", "details": str(erreur), "base_url": BASE_URL},
            ensure_ascii=False,
        )


# ---------------------------------------------------------------------------
# Outils MCP
# ---------------------------------------------------------------------------

@mcp.tool()
async def rechercher(q: str, types: str = "", limite: int = 10) -> str:
    """Recherche globale dans toutes les entités (régions, départements,
    arrondissements, communes, villages, universités, datasets).

    Args:
        q: texte recherché (minimum 2 caractères).
        types: filtre optionnel, codes séparés par des virgules parmi
            region,departement,arrondissement,commune,village,universite,dataset.
        limite: nombre maximum de résultats (défaut 10, max 50).
    """
    return await _get(
        "/api/v1/search/",
        params={"q": q, "types": types, "limit": max(1, min(limite, 50))},
    )


@mcp.tool()
async def lister_regions() -> str:
    """Liste des 14 régions du Sénégal avec P-code, population (RGPH-5 2023),
    superficie et chef-lieu."""
    return await _get("/api/v1/regions/", params={"page_size": 50})


@mcp.tool()
async def obtenir_region(pcode: str) -> str:
    """Détail d'une région par son P-code (ex. SN01 pour Dakar) :
    population, superficie, densité, liste des départements."""
    return await _get(f"/api/v1/regions/{pcode}/")


@mcp.tool()
async def lister_entites(
    niveau: str,
    region_pcode: str = "",
    departement_pcode: str = "",
    q: str = "",
    page_size: int = 50,
) -> str:
    """Liste paginée d'entités administratives avec filtres hiérarchiques.

    Args:
        niveau: un de regions, departements, arrondissements, communes, villages.
        region_pcode: filtre par région (ex. SN09 pour Matam).
        departement_pcode: filtre par département (ex. SN0901 pour Kanel).
        q: recherche par nom (2 caractères minimum).
        page_size: résultats par page (max 200).
    """
    niveaux = ("regions", "departements", "arrondissements", "communes", "villages")
    if niveau not in niveaux:
        return json.dumps({"erreur": f"niveau invalide, choisir parmi {niveaux}"})
    params = {
        "region": region_pcode or None,
        "departement": departement_pcode or None,
        "search": q or None,
        "page_size": max(1, min(page_size, 200)),
    }
    return await _get(f"/api/v1/{niveau}/", params=params)


@mcp.tool()
async def statistiques_nationales() -> str:
    """Agrégats nationaux : population totale (RGPH-5 2023), densités,
    comptages géographiques, entités géoréférencées."""
    return await _get("/api/v1/statistics/")


@mcp.tool()
async def statistiques_region(pcode: str) -> str:
    """Statistiques détaillées d'une région (ex. SN01) : population,
    superficie, densité, départements, communes, villages."""
    return await _get(f"/api/v1/statistics/regions/{pcode}/")


@mcp.tool()
async def production_agricole(
    element: str = "production_tonnes",
    culture: str = "",
    annee_min: int = 0,
    annee_max: int = 0,
    ordre: str = "-valeur",
    page_size: int = 15,
) -> str:
    """Production agricole FAOSTAT du Sénégal (1961-2024).

    Args:
        element: production_tonnes, superficie_ha ou rendement.
        culture: filtre par nom de culture (ex. Groundnuts, Rice, Millet).
        annee_min / annee_max: bornes d'années incluses.
        ordre: tri (défaut -valeur = plus grosses productions d'abord).
    """
    return await _get(
        "/api/v1/agriculture/production/",
        params={
            "element": element,
            "culture__nom__icontains": culture or None,
            "annee_min": annee_min or None,
            "annee_max": annee_max or None,
            "ordering": ordre,
            "page_size": max(1, min(page_size, 200)),
        },
    )


@mcp.tool()
async def indicateurs_economiques(code: str = "", annee_min: int = 0) -> str:
    """Indicateurs macroéconomiques Banque mondiale du Sénégal (1960-2025).

    Args:
        code: si renseigné (ex. NY.GDP.MKTP.CD pour le PIB, FP.CPI.TOTL.ZG
            pour l'inflation, NY.GDP.MKTP.KD.ZG pour la croissance), renvoie
            les observations de cet indicateur ; sinon la liste des 21
            indicateurs suivis avec leur dernière valeur.
        annee_min: année de début (observations uniquement).
    """
    if code:
        return await _get(
            "/api/v1/economie/observations/",
            params={"indicateur": code, "annee_min": annee_min or None,
                    "ordering": "-annee", "page_size": 100},
        )
    return await _get("/api/v1/economie/indicateurs/", params={"page_size": 50})


@mcp.tool()
async def stations_climatiques() -> str:
    """Liste des 14 stations météo GHCN du Sénégal (identifiant, nom,
    coordonnées, altitude)."""
    return await _get("/api/v1/climat/stations/", params={"page_size": 50})


@mcp.tool()
async def observations_climatiques(
    station: str = "",
    annee_min: int = 0,
    annee_max: int = 0,
    page_size: int = 50,
) -> str:
    """Observations climatiques mensuelles NOAA (1950-2025) : températures
    moyenne/min/max et précipitations.

    Args:
        station: identifiant GHCN (ex. SG000061641 pour Dakar/Yoff) —
            utiliser stations_climatiques() pour lister les identifiants.
        annee_min / annee_max: bornes d'années incluses.
    """
    return await _get(
        "/api/v1/climat/observations/",
        params={
            "station": station or None,
            "annee_min": annee_min or None,
            "annee_max": annee_max or None,
            "ordering": "annee,mois",
            "page_size": max(1, min(page_size, 200)),
        },
    )


@mcp.tool()
async def demographie(annee: int = 2023, niveau: str = "region") -> str:
    """Population officielle RGPH-5 (ANSD) par région ou département.

    Args:
        annee: année du recensement (2023).
        niveau: region ou departement.
    """
    return await _get(
        "/api/v1/demographie/population/",
        params={"annee": annee, "niveau": niveau, "ordering": "-population",
                "page_size": 100},
    )


@mcp.tool()
async def jeux_de_donnees() -> str:
    """Catalogue des jeux de données : source, licence, période couverte,
    nombre d'enregistrements et formats de téléchargement."""
    return await _get("/api/v1/datasets/", params={"page_size": 50})


if __name__ == "__main__":
    mcp.run()
