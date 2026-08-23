from django.core.management.base import BaseCommand

from datasets import catalog
from datasets.models import DataQualityReport, DataSource, Dataset, DatasetVersion


class Command(BaseCommand):
    help = 'Synchronise le catalogue de datasets (sources, datasets, versions, qualité).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les actions sans écrire en base.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        counts = catalog._record_counts()
        missing_coords = catalog._missing_coords()

        for entry in catalog.CATALOG:
            source_data = entry['source']
            if dry_run:
                self.stdout.write(f"[dry-run] Source : {source_data['nom']} ({source_data['slug']})")
                dataset_objs = []
                for ds_data in entry['datasets']:
                    slug = ds_data['slug']
                    record_count = counts.get(slug)
                    self.stdout.write(
                        f"  [dry-run] Dataset : {ds_data['titre']} ({slug}) "
                        f"— record_count={record_count}"
                    )
                    dataset_objs.append(None)
                continue
            source_obj, created = DataSource.objects.update_or_create(
                slug=source_data['slug'],
                defaults={
                    'nom': source_data['nom'],
                    'url': source_data['url'],
                    'publisher': source_data.get('publisher', ''),
                    'license_nom': source_data['license_nom'],
                    'license_url': source_data.get('license_url', ''),
                    'redistribuable': source_data.get('redistribuable', True),
                },
            )
            self.stdout.write(
                f"{'Créée' if created else 'Mise à jour'} : "
                f"Source {source_obj.nom} (slug={source_obj.slug})"
            )

            for ds_data in entry['datasets']:
                slug = ds_data['slug']
                description = ds_data['description']
                if callable(description):
                    description = description(counts)
                defaults = {
                    'titre': ds_data['titre'],
                    'description': description,
                    'categorie': ds_data['categorie'],
                    'source': source_obj,
                    'coverage_period': ds_data.get('coverage_period', ''),
                    'update_frequency': ds_data.get('update_frequency', ''),
                    'export_formats': ds_data.get('export_formats', []),
                    'methodology': ds_data.get('methodology', ''),
                }
                dataset_obj, created = Dataset.objects.update_or_create(
                    slug=slug, defaults=defaults
                )
                self.stdout.write(
                    f"  {'Créé' if created else 'Mis à jour'} : "
                    f"Dataset {dataset_obj.titre} (slug={slug})"
                )
                record_count = counts.get(slug)
                version_obj, version_created = DatasetVersion.objects.update_or_create(
                    dataset=dataset_obj,
                    version_number='1.0.0',
                    defaults={'record_count': record_count},
                )
                self.stdout.write(
                    f"    Version {'créée' if version_created else 'mise à jour'} : "
                    f"{version_obj.version_number} — record_count={record_count}"
                )
                report = DataQualityReport.objects.create(
                    version=version_obj,
                    valid=record_count or 0,
                    warnings=0,
                    errors=0,
                    duplicates=0,
                    missing_coords=missing_coords if slug == 'sen-admin-boundaries' else 0,
                    details={'generated_by': 'sync_datasets'},
                )
                self.stdout.write(f'    Rapport qualité #{report.pk} créé.')

        total = sum(counts.values())
        mode = '[dry-run] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'{mode}Synchronisation terminée : {len(catalog.CATALOG)} sources, '
            f'{sum(len(e["datasets"]) for e in catalog.CATALOG)} datasets, '
            f'{total} enregistrements au total.'
        ))
