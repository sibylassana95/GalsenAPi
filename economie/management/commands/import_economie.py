"""Import des indicateurs économiques World Bank (Sénégal) : GET API,
cache JSON, parse, upsert IndicateurEconomique + ObservationEconomique."""
from datetime import datetime, timezone
from pathlib import Path

import economie.worldbank as worldbank
from django.core.management.base import BaseCommand, CommandError

from datasets.models import DataSource
from economie.indicators import INDICATEURS_PAR_CODE, SOURCE_DEFAULTS, url_indicateur


class Command(BaseCommand):
    help = (
        'Importe les indicateurs économiques du Sénégal depuis l\u2019API '
        'World Bank (CC BY 4.0) : upsert IndicateurEconomique + '
        'ObservationEconomique.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--offline', action='store_true',
            help="Utilise uniquement le cache local var/ingest/worldbank/.",
        )
        parser.add_argument(
            '--indicators', default='',
            help='Codes WB à importer séparés par des virgules '
                 '(défaut : tous les codes du curateur).',
        )
        parser.add_argument(
            '--timeout', type=int, default=60,
            help='Timeout HTTP par indicateur en secondes (défaut : 60).',
        )
        parser.add_argument(
            '--cache-dir', default='',
            help='Répertoire cache alternatif (tests / ingénierie).',
        )

    def handle(self, *args, **options):
        if options['cache_dir']:
            worldbank.CACHE_DIR = Path(options['cache_dir'])

        codes = self._codes_demandes(options['indicators'])
        source_obj, created = DataSource.objects.update_or_create(
            slug='worldbank', defaults=SOURCE_DEFAULTS
        )
        self.stdout.write(
            f"{'Créée' if created else 'OK'} : source "
            f"{source_obj.nom} (slug={source_obj.slug}, "
            f"licence {source_obj.license_nom})"
        )
        self.stdout.write(f'Indicateurs demandés : {len(codes)}')

        stats_list = []
        for i, code in enumerate(codes, 1):
            api_url = url_indicateur(code)
            payload = self._payload(code, options)
            parse = worldbank.parse_reponse(payload)
            indicateur, stats = worldbank.importer_indicateur(
                code, parse, source=source_obj, api_url=api_url,
            )
            stats['decimal'] = parse.get('decimal', '')
            stats['lastupdated'] = parse.get('lastupdated', '')
            stats['api_url'] = api_url
            stats_list.append(stats)
            self._rapport_indicateur(i, len(codes), stats)

        self._rapport_global(stats_list)

    def _codes_demandes(self, brut):
        if not brut:
            return list(INDICATEURS_PAR_CODE)
        codes = [c.strip() for c in brut.split(',') if c.strip()]
        inconnus = [c for c in codes if c not in INDICATEURS_PAR_CODE]
        if inconnus:
            raise CommandError(
                f'Codes hors curateur : {", ".join(inconnus)}. '
                'Voir economie/indicators.py.'
            )
        return codes

    def _payload(self, code, options):
        if options['offline']:
            payload = worldbank.lire_cache(code)
            if payload is None:
                raise CommandError(
                    f'--offline mais cache absent pour {code} '
                    f'({worldbank.chemin_cache(code)}). Relancez sans --offline.'
                )
            return payload
        return worldbank.telecharger(code, timeout=options['timeout'])

    def _rapport_indicateur(self, i, total, stats):
        fmt_n = lambda n: f'{n:,}'.replace(',', ' ')
        fmt_d = lambda d: (
            f'{d:,.2f}'.replace(',', ' ').replace('.', ',')
            if d is not None else 'n/a'
        )
        self.stdout.write('')
        self.stdout.write(
            f'[{i}/{total}] {stats["code"]} — {stats["nom"]} '
            f'({"créé" if stats["cree"] else "maj"})'
        )
        self.stdout.write(
            f'  Observations : {fmt_n(stats["observations"])} '
            f'(créées {stats["crees"]}, maj {stats["maj"]}) ; '
            f'sans donnée (null API, écartées) : {stats["sans_donnee"]}'
        )
        if stats['an_min'] is not None:
            self.stdout.write(
                f'  Plage années : {stats["an_min"]}–{stats["an_max"]} ; '
                f'dernière valeur ({stats["an_max"]}) : '
                f'{fmt_d(stats["derniere_valeur"])} '
                f'[WB lastupdated={stats["lastupdated"]}]'
            )
        else:
            self.stdout.write(self.style.WARNING(
                '  Aucune donnée non nulle pour ce code !'
            ))

    def _rapport_global(self, stats_list):
        self.stdout.write('')
        self.stdout.write('=== Rapport import_economie ===')
        total_obs = sum(s['observations'] for s in stats_list)
        total_nulls = sum(s['sans_donnee'] for s in stats_list)
        self.stdout.write(
            f'Indicateurs : {len(stats_list)} ; observations upsertées : '
            f'{total_obs:,}'.replace(',', ' ')
            + f' ; nulls écartés : {total_nulls}'
        )
        pib = next(
            (s for s in stats_list if s['code'] == 'NY.GDP.MKTP.CD'), None
        )
        if pib and pib['derniere_valeur'] is not None:
            valeur = float(pib['derniere_valeur'])
            milliards = valeur / 1_000_000_000
            self.stdout.write(
                f'Contrôle PIB : NY.GDP.MKTP.CD {pib["an_max"]} = '
                f'{milliards:.2f} Md US$'
            )
            bas, haut = worldbank.PLAGE_PIB_USD
            if not (bas <= valeur <= haut):
                self.stdout.write(self.style.WARNING(
                    f'INCOHÉRENCE : PIB hors plage plausible '
                    f'[{bas/1e9:.0f}; {haut/1e9:.0f}] Md US$ — vérifiez la source.'
                ))
            else:
                self.stdout.write('Contrôle PIB : cohérent.')
        horodatage = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        self.stdout.write(f'Import terminé à {horodatage}.')
