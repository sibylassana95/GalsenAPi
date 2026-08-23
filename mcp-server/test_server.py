"""Tests du serveur MCP GalsenAPI — transport HTTP simulé, jamais de réseau."""

import json

import httpx
import pytest

import server


@pytest.fixture()
def transport(monkeypatch):
    """Injecte un transport httpx simulé piloté par un dict route -> réponse."""
    routes = {}

    def handler(requete: httpx.Request) -> httpx.Response:
        chemin = requete.url.path
        if chemin in routes:
            return routes[chemin](requete)
        return httpx.Response(404, json={"detail": "introuvable"})

    server._transport = httpx.MockTransport(handler)
    yield routes
    server._transport = None


@pytest.mark.asyncio
async def test_rechercher_formate_les_resultats(transport):
    transport["/api/v1/search/"] = lambda req: httpx.Response(
        200,
        json={"count": 1, "results": [{"type": "departement", "nom": "Kanel"}]},
    )
    sortie = json.loads(await server.rechercher("kanel"))
    assert sortie["results"][0]["nom"] == "Kanel"


@pytest.mark.asyncio
async def test_rechercher_erreur_http(transport):
    sortie = json.loads(await server.rechercher("kanel"))
    assert sortie["erreur"] == "HTTP 404"


@pytest.mark.asyncio
async def test_lister_entites_niveau_invalide(transport):
    sortie = json.loads(await server.lister_entites("pouet"))
    assert "niveau invalide" in sortie["erreur"]


@pytest.mark.asyncio
async def test_lister_entites_construit_les_parametres(transport):
    captés = {}

    def capte(req: httpx.Request) -> httpx.Response:
        captés.update(dict(req.url.params))
        return httpx.Response(200, json={"count": 0, "results": []})

    transport["/api/v1/communes/"] = capte
    await server.lister_entites(
        "communes", region_pcode="SN09", q="kanel", page_size=500
    )
    assert captés["region"] == "SN09"
    assert captés["search"] == "kanel"
    assert captés["page_size"] == "200"  # borné au maximum


@pytest.mark.asyncio
async def test_indicateurs_avec_code_interroge_les_observations(transport):
    appelé = []

    def capte(req: httpx.Request) -> httpx.Response:
        appelé.append(req.url.path)
        return httpx.Response(200, json={"count": 1, "results": [{"annee": 2025}]})

    transport["/api/v1/economie/observations/"] = capte
    sortie = json.loads(await server.indicateurs_economiques("NY.GDP.MKTP.CD"))
    assert sortie["results"][0]["annee"] == 2025
    assert appelé == ["/api/v1/economie/observations/"]


@pytest.mark.asyncio
async def test_api_injoignable(transport, monkeypatch):
    def echec(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refusé")

    transport["/api/v1/statistics/"] = echec
    sortie = json.loads(await server.statistiques_nationales())
    assert sortie["erreur"] == "API injoignable"


@pytest.mark.asyncio
async def test_outils_declares():
    """Tous les outils attendus sont bien exposés au protocole MCP."""
    outils = await server.mcp.list_tools()
    noms = {outil.name for outil in outils}
    attendus = {
        "rechercher",
        "lister_regions",
        "obtenir_region",
        "lister_entites",
        "statistiques_nationales",
        "statistiques_region",
        "production_agricole",
        "indicateurs_economiques",
        "stations_climatiques",
        "observations_climatiques",
        "demographie",
        "jeux_de_donnees",
    }
    assert attendus <= noms
