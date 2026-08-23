"""Import GHCN-Daily (NOAA NCEI) pour les stations du Sénégal :
inventaire fixed-width -> CSV par station -> agrégats mensuels upsertés.
"""
from datetime import datetime, timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from climat import ghcn
from datasets.models import DataSource


class Command(BaseCommand):
    help = (
        'Importe les observations climatiques du Sénégal depuis '
        'GHCN-Daily (NOAA NCEI, domaine public) : inventaire des '
        'stations SG, CSV journaliers par station, agrégation mensuelle '
        '(moyennes températures, somme précipitations), upsert '
        'idempotent StationClimatique + ObservationMensuelle.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--offline', action='store_true',
            help='Utilise uniquement le cache local var/ingest/noaa/.',
        )
        parser.add_argument(
            '--from-annee', type=int, default=1901,
            help="Année de début de l'historique importé (défaut : 1901).",
        )
        parser.add_argument(
            '--timeout', type=int, default=120,
            help='Timeout HTTP en secondes par téléchargement '
                 '(défaut : 120).',
        )
        parser.add_argument(
            '--cache-dir', default='',
            help='Répertoire cache alternatif (tests / ingénierie).',
        )

    def handle(self, *args, **options):
        if options['cache_dir']:
            ghcn.CACHE_DIR = Path(options['cache_dir'])

        source_obj, created = DataSource.objects.update_or_create(
            slug='noaa-ghcn', defaults=ghcn.SOURCE_DEFAULTS,
        )
        self.stdout.write(
            f"{'Créée' if created else 'OK'} : source {source_obj.nom} "
            f"(slug={source_obj.slug}, licence {source_obj.license_nom})"
        )

        texte_inventaire = self._inventaire(options)
        stations = ghcn.parse_stations(texte_inventaire)
        if not stations:
            raise CommandError(
                "Aucune station sénégalaise dans l'inventaire GHCN — "
                'vérifiez le fichier source.'
            )
        self.stdout.write(f'Stations Sénégal trouvées : {len(stations)}')
        for station_data in stations:
            altitude = station_data['altitude']
            self.stdout.write(
                f"  - {station_data['station_id']} "
                f"{station_data['nom']} "
                f"(lat {station_data['latitude']}, lon "
                f"{station_data['longitude']}, alt "
                f"{altitude if altitude is not None else 'n/a'} m)"
            )

        stats_list = []
        echecs = []
        total = len(stations)
        for i, station_data in enumerate(stations, 1):
            try:
                stats = self._importe_station(station_data, source_obj,
                                              options)
            except Exception as erreur:
                echecs.append((station_data['station_id'], str(erreur)))
                self.stdout.write(self.style.WARNING(
                    f"[{i}/{total}] ÉCHEC {station_data['station_id']} : "
                    f'{erreur} — station suivante.'
                ))
                continue
            stats_list.append(stats)
            self._rapport_station(i, total, stats)

        self._rapport_global(stats_list, echecs)

    def _inventaire(self, options):
        if options['offline']:
            texte = ghcn.lire_inventaire_cache()
            if texte is None:
                raise CommandError(
                    '--offline mais inventaire absent '
                    f'({ghcn.chemin_cache_stations()}). Relancez sans '
                    '--offline.'
                )
            return texte
        return ghcn.telecharger_inventaire(timeout=options['timeout'])

    def _csv_journalier(self, station_id, options):
        chemin = ghcn.lire_station_csv_cache(station_id)
        if chemin is None:
            if options['offline']:
                raise CommandError(
                    f"--offline mais cache absent pour {station_id} "
                    f'({ghcn.chemin_cache_station(station_id)}).'
                )
            chemin = ghcn.telecharger_station_csv(
                station_id, timeout=options['timeout'],
            )
        return chemin

    def _importe_station(self, station_data, source_obj, options):
        from_annee = options['from_annee']
        chemin = self._csv_journalier(station_data['station_id'], options)
        lignes = ghcn.parser_journalier(chemin)
        agrege = ghcn.agreer_mensuel(lignes, from_annee=from_annee)
        _, stats = ghcn.importer_station(station_data, agrege,
                                         source=source_obj)
        stats['controles'] = ghcn.controle_realisme(agrege)
        stats['lignes_source'] = sum(
            1 for ligne in lignes if ligne['annee'] >= from_annee
        )
        return stats

    def _rapport_station(self, i, total, stats):
        controles = stats['controles']
        fmt_d = lambda d: str(d).replace('.', ',') if d is not None else 'n/a'
        self.stdout.write('')
        self.stdout.write(
            f"[{i}/{total}] {stats['station_id']} — {stats['nom']} "
            f"({'créée' if stats['cree'] else 'maj'})"
        )
        self.stdout.write(
            f"  Lignes journalières utilisées : {stats['lignes_source']:,}"
            .replace(',', ' ')
        )
        self.stdout.write(
            f"  Plage années : {stats['an_min']}–{stats['an_max']} ; "
            f"mois upsertés : {stats['crees'] + stats['maj']} "
            f"(créés {stats['crees']}, maj {stats['maj']})"
        )
        mois_avec_tavg = sum(
            1 for mesures in stats['agrege'].values()
            if mesures['tavg'] is not None
        )
        total_mois = len(stats['agrege'])
        pct = (100 * mois_avec_tavg / total_mois) if total_mois else 0
        self.stdout.write(
            f'  Mois avec tavg : {mois_avec_tavg}/{total_mois} ({pct:.0f} %)'
        )
        self.stdout.write(
            f'  Précipitations annuelles moyennes (récent) : '
            f'{fmt_d(controles["prcp_moyen_recent"])} mm/an'
        )
        self.stdout.write(
            f'  Température moyenne annuelle : '
            f'{fmt_d(controles["tavg_moyen"])} °C'
        )
        for anomalie in controles['anomalies']:
            self.stdout.write(self.style.WARNING(
                f'  INCOHÉRENCE SIGNALÉE : {anomalie} (données conservées '
                'telles quelles, à vérifier à la source).'
            ))

    def _rapport_global(self, stats_list, echecs):
        horodatage = datetime.now(timezone.utc).strftime(
            '%Y-%m-%d %H:%M UTC'
        )
        total_obs = sum(s['crees'] + s['maj'] for s in stats_list)
        self.stdout.write('')
        self.stdout.write('=== Rapport import_climat ===')
        self.stdout.write(
            f'Stations importées : {len(stats_list)} ; '
            f'mois upsertés : {total_obs:,}'.replace(',', ' ')
        )
        if echecs:
            self.stdout.write(self.style.WARNING(
                'Stations en échec (ignorées) : '
                + '; '.join(f'{sid} ({erreur})' for sid, erreur in echecs)
            ))
        self.stdout.write(f'Import terminé à {horodatage}.')
