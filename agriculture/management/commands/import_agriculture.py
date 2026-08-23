"""Import du bulk FAOSTAT QCL (Sénégal) : téléchargement, parse streaming, upsert."""
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from agriculture import faostat
from datasets.models import DataSource


class Command(BaseCommand):
    help = (
        'Importe la production agricole FAOSTAT (QCL) pour le Sénégal depuis le '
        'bulk officiel normalisé : upsert Culture + ProductionAgricole.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--offline', action='store_true',
            help="Utilise uniquement le cache local var/ingest/faostat/.",
        )
        parser.add_argument(
            '--years-from', type=int, default=1961,
            help='Année de début (défaut : 1961, historique complet).',
        )
        parser.add_argument(
            '--timeout', type=int, default=300,
            help='Timeout du téléchargement en secondes (défaut : 300).',
        )
        parser.add_argument(
            '--fichier', default='',
            help='Zip FAOSTAT local (contourne le téléchargement).',
        )

    def handle(self, *args, **options):
        zip_path = self._resoudre_zip(options)
        meta_base = {
            'bulk_dataset': faostat.BULK_URL,
            'downloaded_at': datetime.fromtimestamp(
                zip_path.stat().st_mtime, tz=timezone.utc
            ).isoformat(),
            'fichier': zip_path.name,
        }

        source_obj, created = DataSource.objects.update_or_create(
            slug='faostat', defaults=faostat.SOURCE_DEFAULTS
        )
        self.stdout.write(
            f"{'Créée' if created else 'OK'} : source "
            f"{source_obj.nom} (slug={source_obj.slug})"
        )
        self.stdout.write(f'Archive : {zip_path}')
        self.stdout.write(f'Zone filtrée : {faostat.AREA_NAME} ; '
                          f'années >= {options["years_from"]}')

        with zipfile.ZipFile(zip_path) as archive:
            membre = faostat.membre_donnees(zip_path)
            with archive.open(membre) as flux:
                lignes = (
                    l for l in faostat.lignes_normalisees(flux)
                    if l['area'] == faostat.AREA_NAME
                )
                stats = faostat.importer_lignes(
                    lignes, source=source_obj,
                    years_from=options['years_from'], meta_base=meta_base,
                )

        self._rapport(stats)

    def _resoudre_zip(self, options):
        fichier = options.get('fichier')
        if fichier:
            path = Path(fichier)
            if not path.is_absolute():
                path = Path(settings.BASE_DIR) / path
            if not path.exists():
                raise CommandError(f'Fichier introuvable : {path}')
            return path
        cache = faostat.chemin_cache()
        if options['offline']:
            if not (cache.exists() and cache.stat().st_size > 0):
                raise CommandError(
                    f'--offline mais cache absent : {cache}. '
                    'Relancez sans --offline pour télécharger.'
                )
            return cache
        return faostat.telecharger_bulk(timeout=options['timeout'])

    def _rapport(self, stats):
        fmt = lambda n: f'{n:,}'.replace(',', ' ')
        self.stdout.write('')
        self.stdout.write('=== Rapport import_agriculture ===')
        self.stdout.write(
            f'Cultures/produits : {stats["cultures_total"]} '
            f'(dont {stats["cultures_creees"]} créées)'
        )
        total = 0
        for element in ('production_tonnes', 'superficie_recoltee_ha',
                        'rendement_hg_ha'):
            n = stats['compteurs'].get(element, 0)
            total += n
            self.stdout.write(f'Lignes {element} : {fmt(n)}')
        self.stdout.write(f'Records upsertés : {fmt(total)} '
                          f'(créés : {fmt(stats["crees"])}, '
                          f'maj : {fmt(stats["maj"])})')
        if stats['an_min'] is not None:
            self.stdout.write(
                f"Plage d'années : {stats['an_min']}–{stats['an_max']}"
            )
        ignores = stats.get('ignores_elements') or {}
        if ignores:
            detail = ', '.join(f'{k} ({v})' for k, v in sorted(ignores.items()))
            self.stdout.write(self.style.WARNING(
                f'Éléments/unités ignorés : {detail}'
            ))

        from agriculture.models import ProductionAgricole
        derniere = (ProductionAgricole.objects
                    .filter(element='production_tonnes')
                    .order_by('-annee').values_list('annee', flat=True).first())
        if derniere:
            self.stdout.write(
                f'Top 5 cultures {derniere} (production, tonnes) :'
            )
            top5 = (ProductionAgricole.objects
                    .filter(element='production_tonnes', annee=derniere,
                            valeur__isnull=False)
                    .select_related('culture').order_by('-valeur')[:5])
            for i, prod in enumerate(top5, 1):
                self.stdout.write(
                    f'  {i}. {prod.culture.nom} : {fmt(round(prod.valeur))}'
                )
