"""Rattachement officiel des communes aux départements (ANSD, RGPH-5 2023)."""

from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from geo import ansd
from geo.models import Commune, Departement
from geo.utils import slug_nom


class Command(BaseCommand):
    help = (
        "Importe le rattachement officiel des communes à leur département et la "
        "population RGPH-5 par commune (Répertoire des localités, ANSD 2023)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--offline",
            action="store_true",
            help="Utilise uniquement le cache var/ingest/ansd/.",
        )
        parser.add_argument(
            "--fichier",
            default=str(Path("var") / "ingest" / "ansd" / "repertoire_2023.csv"),
            help="Chemin du CSV du répertoire (défaut : cache var/ingest/ansd/).",
        )
        parser.add_argument(
            "--timeout", type=int, default=300,
            help="Timeout du téléchargement en secondes (défaut : 300).",
        )

    def handle(self, *args, **options):
        chemin_cache = Path(options["fichier"])
        if options["offline"]:
            if not chemin_cache.exists():
                self.stderr.write(
                    "Cache absent : lancez la commande sans --offline une première fois."
                )
                return
        else:
            self.stdout.write("Téléchargement du répertoire des localités (ANSD)…")
            ansd.telecharger(chemin_cache, timeout=options["timeout"])

        communes_anasd = ansd.communes_agregrees(chemin_cache)
        self.stdout.write(f"Communes distinctes dans le répertoire : {len(communes_anasd)}")

        # Index des départements par (slug région, slug département)
        departements_par_slug = {
            (slug_nom(d.region.nom), slug_nom(d.nom)): d
            for d in Departement.objects.select_related("region")
        }

        # Index des communes existantes par (id département, slug nom)
        communes_existantes: dict[tuple[int, str], Commune] = {
            (c.departement_id, slug_nom(c.nom)): c
            for c in Commune.objects.all()
        }

        importes, mises_a_jour, ignorees = 0, 0, []
        a_creer = []
        with transaction.atomic():
            for entree in communes_anasd:
                cle_dept = (
                    slug_nom(entree["region"]),
                    self._slug_departement_ansd(
                        entree["region"], entree["departement"]
                    ),
                )
                departement = departements_par_slug.get(cle_dept)
                if departement is None:
                    ignorees.append(entree)
                    continue

                meta = {
                    "population_source": ansd.POPULATION_SOURCE,
                    "source_url": ansd.SOURCE_URL,
                    "com_arrt_ville": entree["com_arrt_ville"],
                    "region_ansd": entree["region"],
                    "nb_localites": entree["nb_localites"],
                }
                cle_commune = (departement.id, slug_nom(entree["commune"]))
                existante = communes_existantes.get(cle_commune)
                if existante:
                    existante.population = entree["population"]
                    existante.type = "commune"
                    existante.meta = meta
                    existante.save(update_fields=["population", "type", "meta"])
                    mises_a_jour += 1
                else:
                    commune = Commune(
                        departement=departement,
                        nom=entree["commune"],
                        type="commune",
                        population=entree["population"],
                        meta=meta,
                    )
                    a_creer.append(commune)
                    communes_existantes[cle_commune] = commune
                    importes += 1
            Commune.objects.bulk_create(a_creer, batch_size=500)

        total = Commune.objects.count()
        rattachees = Commune.objects.exclude(departement__isnull=True).count()
        self.stdout.write(
            f"Créées : {importes} | mises à jour : {mises_a_jour} | "
            f"ignorées (département introuvable) : {len(ignorees)}"
        )
        for entree in ignorees[:10]:
            self.stdout.write(
                f"  ignorée : {entree['commune']} ({entree['departement']} / {entree['region']})"
            )
        self.stdout.write(f"Total communes : {total} | rattachées à un département : {rattachees}")
        self.stdout.write(f"Source : {ansd.SOURCE_URL}")

    @staticmethod
    def _slug_departement_ansd(region_ansd: str, departement_ansd: str) -> str:
        """Slug du département ANSD, avec aliasing des variantes orthographiques."""
        slug = slug_nom(departement_ansd)
        return ansd.ALIASES_DEPARTEMENTS.get(slug, slug)
