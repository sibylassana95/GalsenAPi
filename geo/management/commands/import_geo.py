from django.core.management.base import BaseCommand

from geo import ingest


class Command(BaseCommand):
    help = "Importe les limites administratives HDX COD-AB et les données legacy."

    def add_arguments(self, parser):
        parser.add_argument('--offline', action='store_true',
                            help="Utilise uniquement le cache var/ingest/codab/.")
        parser.add_argument('--with-legacy', action='store_true', default=True,
                            help='(défaut) Inclut commune.json et village.json.')
        parser.add_argument('--no-legacy', dest='with_legacy', action='store_false',
                            help='Ignore les JSON legacy.')

    def handle(self, *args, **options):
        report = ingest.ImportReport()
        zip_path = ingest.download_codab(report, offline=options['offline'])
        levels = ingest.extract_levels(zip_path)
        self.stdout.write(f"Niveaux détectés: {sorted(levels)}")
        features_by_level = {
            level: ingest.load_features(path)
            for level, path in levels.items()
            if level in (1, 2, 3)
        }
        ingest.import_codab(features_by_level, report)
        if options['with_legacy']:
            ingest.import_legacy(report)
        ingest.validate(report)
        path = report.save()
        self.stdout.write(report.text())
        self.stdout.write(self.style.SUCCESS(f"Rapport écrit: {path}"))
