"""Ingestion du Répertoire des localités RGPH-5 2023 (ANSD).

Source officielle : https://www.ansd.sn/donnees-recensements
Export CSV public : https://www.ansd.sn/data-recensement.csv?field_liste_annee_value=2023&_format=csv

Le fichier liste chaque localité (quartier/village/hameau) avec sa hiérarchie
complète Région → Département → Commune/Commune d'arrondissement/Ville → localité
et les populations du RGPH-5 2023. L'agrégation des localités par commune fournit
le rattachement officiel des ~553 communes à leur département, avec population.

Licence : CC BY 4.0 (revendiquée par l'ANSD / anads.ansd.sn).
"""

import csv
from collections import defaultdict
from pathlib import Path

import requests

URL_REPERTOIRE = (
    "https://www.ansd.sn/data-recensement.csv"
    "?field_liste_annee_value=2023&_format=csv"
)
SOURCE_URL = "https://www.ansd.sn/donnees-recensements"
POPULATION_SOURCE = "RGPH-5 2023 (ANSD, Répertoire des localités)"

# Variantes orthographiques ANSD → libellés HDX COD-AB (clé = slug ANSD)
ALIASES_DEPARTEMENTS = {
    "malem-hoddar": "malem-hodar",
    "nioro": "nioro-du-rip",
    "medina-yoro-foulah": "medina-yorofoula",
    "ranerou-ferlo": "ranerou",
    "koupentoum": "koumpentoum",
}


def telecharger(chemin_cache: Path, timeout: int = 300) -> Path:
    """Télécharge le CSV du répertoire dans le cache local (si absent)."""
    if chemin_cache.exists() and chemin_cache.stat().st_size > 0:
        return chemin_cache
    chemin_cache.parent.mkdir(parents=True, exist_ok=True)
    reponse = requests.get(URL_REPERTOIRE, timeout=timeout)
    reponse.raise_for_status()
    chemin_cache.write_bytes(reponse.content)
    return chemin_cache


def communes_agregrees(chemin_cache: Path) -> list[dict]:
    """Agrège les localités par commune.

    Retourne une liste de dicts :
    {region, departement, com_arrt_ville, commune, population, nb_localites}
    """
    populations = defaultdict(int)
    localites = defaultdict(int)
    with open(chemin_cache, encoding="utf-8-sig", newline="") as fichier:
        for ligne in csv.DictReader(fichier):
            cle = (
                ligne["Region"].strip(),
                ligne["Departement"].strip(),
                ligne["COM_ARRT_VILLE"].strip(),
                ligne["COMMUNE"].strip(),
            )
            if not all(cle):
                continue
            populations[cle] += int(ligne["POPULATION"] or 0)
            localites[cle] += 1
    return [
        {
            "region": region,
            "departement": departement,
            "com_arrt_ville": com_arrt_ville,
            "commune": commune,
            "population": populations[(region, departement, com_arrt_ville, commune)],
            "nb_localites": localites[(region, departement, com_arrt_ville, commune)],
        }
        for (region, departement, com_arrt_ville, commune), pop in sorted(
            populations.items()
        )
        for pop in [pop]
    ]
