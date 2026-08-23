"""Import des chiffres de population RGPH-5 2023 (ANSD) depuis data/rgph5_2023.json."""
import json
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from datasets.models import DataSource
from demographie.models import PopulationRecord
from geo.models import Departement, Region
from geo.utils import repair_mojibake, slug_nom

# Variantes de nommage RGPH-5 -> slugs HDX utilisés dans geo.Departement.nom.
DEPARTEMENT_SLUG_ALIASES = {
    'malem-hoddar': 'malem-hodar',
    'medina-yoro-foulah': 'medina-yorofoula',
    'nioro': 'nioro-du-rip',
}

SOURCE_DEFAULTS = {
    'nom': 'ANSD',
    'url': 'https://www.ansd.sn',
    'publisher': 'Agence Nationale de la Statistique et de la Démographie',
    'license_nom': 'CC BY 4.0',
    'license_url': 'https://anads.ansd.sn',
    'redistribuable': True,
}


def _slug(texte, aliases=None):
    brut = str(repair_mojibake(texte) or texte or '').strip()
    clef = slug_nom(brut)
    if aliases:
        return aliases.get(clef, clef)
    return clef


def _entier(valeur):
    if valeur is None:
        return None
    return int(str(valeur).strip())


class Command(BaseCommand):
    help = (
        'Importe la population RGPH-5 2023 (ANSD) : upsert PopulationRecord puis '
        'rafraîchit geo.Region.population et geo.Departement.population.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--fichier',
            default='data/rgph5_2023.json',
            help='Chemin du JSON source (défaut : data/rgph5_2023.json).',
        )
        parser.add_argument(
            '--no-refresh-geo',
            action='store_true',
            help='Ne met pas à jour geo.Region / geo.Departement.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options['fichier'])
        if not path.is_absolute():
            path = Path(settings.BASE_DIR) / path
        if not path.exists():
            raise CommandError(f'Fichier introuvable : {path}')
        data = json.loads(path.read_bytes())
        meta = data.get('meta') or {}
        regions_data = data.get('regions') or []
        departements_data = data.get('departements') or []
        annee = int(meta.get('annee', 2023))
        total_national = meta.get('total_national')
        value_type = meta.get('value_type', 'officielle')

        source_obj, created = DataSource.objects.update_or_create(
            slug='ansd', defaults=SOURCE_DEFAULTS
        )
        self.stdout.write(
            f"{'Créée' if created else 'OK'} : source ANSD (slug=ansd)"
        )
        self.stdout.write(f'Fichier : {path}')
        self.stdout.write(
            f'Entrées lues : {len(regions_data)} régions, '
            f'{len(departements_data)} départements (année {annee})'
        )

        regions_index = {slug_nom(r.nom): r for r in Region.objects.all()}
        depts_qs = Departement.objects.select_related('region')
        depts_index = {
            (slug_nom(d.region.nom), slug_nom(d.nom)): d for d in depts_qs
        }

        import_stamp = datetime.now(timezone.utc).isoformat()
        base_meta = {
            'source': 'RGPH-5 2023 (ANSD)',
            'fichier': path.name,
            'date_import': import_stamp,
        }

        regions_ok, regions_manquantes = [], []
        for entry in regions_data:
            nom_brut = entry.get('nom') or ''
            region = regions_index.get(_slug(nom_brut))
            if region is None:
                regions_manquantes.append(nom_brut)
                continue
            record_meta = dict(base_meta, tableau='I-21 (rapport définitif Thème I)')
            PopulationRecord.objects.update_or_create(
                entity_type='region',
                region=region,
                departement=None,
                annee=annee,
                defaults={
                    'population': _entier(entry.get('population')),
                    'hommes': _entier(entry.get('hommes')),
                    'femmes': _entier(entry.get('femmes')),
                    'value_type': value_type,
                    'source': source_obj,
                    'meta': record_meta,
                },
            )
            regions_ok.append((region, _entier(entry.get('population'))))

        depts_ok, depts_manquants = [], []
        for entry in departements_data:
            nom_brut = entry.get('nom') or ''
            region_brut = entry.get('region') or ''
            dept = depts_index.get((_slug(region_brut), _slug(nom_brut, DEPARTEMENT_SLUG_ALIASES)))
            if dept is None:
                depts_manquants.append(f'{nom_brut} ({region_brut})')
                continue
            record_meta = dict(base_meta, tableau='I-9 (rapport définitif Thème I)')
            PopulationRecord.objects.update_or_create(
                entity_type='departement',
                region=dept.region,
                departement=dept,
                annee=annee,
                defaults={
                    'population': _entier(entry.get('population')),
                    'hommes': _entier(entry.get('hommes')),
                    'femmes': _entier(entry.get('femmes')),
                    'value_type': value_type,
                    'source': source_obj,
                    'meta': record_meta,
                },
            )
            depts_ok.append((dept, _entier(entry.get('population'))))

        if not options['no_refresh_geo']:
            for region, population in regions_ok:
                meta_region = dict(region.meta or {})
                meta_region['population_source'] = 'RGPH-5 2023 (ANSD)'
                region.population = population
                region.meta = meta_region
                region.save(update_fields=['population', 'meta'])
            for dept, population in depts_ok:
                meta_dept = dict(dept.meta or {})
                meta_dept['population_source'] = 'RGPH-5 2023 (ANSD)'
                dept.population = population
                dept.meta = meta_dept
                dept.save(update_fields=['population', 'meta'])

        self._rapport(regions_ok, regions_manquantes, depts_ok, depts_manquants,
                      total_national, options['no_refresh_geo'])

    def _rapport(self, regions_ok, regions_manquantes, depts_ok, depts_manquants,
                 total_national, no_refresh):
        self.stdout.write('')
        self.stdout.write('=== Rapport import_demographie ===')
        self.stdout.write(f'Régions importées : {len(regions_ok)}')
        if regions_manquantes:
            self.stdout.write(self.style.WARNING(
                f'Régions NON résolues en base ({len(regions_manquantes)}) : '
                + ', '.join(regions_manquantes)
            ))
        self.stdout.write(f'Départements importés : {len(depts_ok)}')
        if depts_manquants:
            self.stdout.write(self.style.WARNING(
                f'Départements NON résolus en base ({len(depts_manquants)}) : '
                + ', '.join(depts_manquants)
            ))

        somme_regions = sum(pop for _, pop in regions_ok if pop is not None)
        somme_depts = sum(pop for _, pop in depts_ok if pop is not None)
        self.stdout.write('')
        self.stdout.write('=== Contrôle des totaux ===')
        self.stdout.write(f'Somme régions importées : {_fmt(somme_regions)}')
        self.stdout.write(f'Somme départements importés : {_fmt(somme_depts)}')
        ecart_niveaux = somme_depts - somme_regions
        statut = 'OK' if ecart_niveaux == 0 else 'ÉCART'
        self.stdout.write(
            f'Écart départements - régions : {_fmt(ecart_niveaux)} [{statut}]'
        )
        if total_national is not None:
            ecart_national = somme_regions - int(total_national)
            statut = 'OK' if ecart_national == 0 else 'ÉCART'
            self.stdout.write(self.style.WARNING(
                f'Écart somme régions - total national ({_fmt(int(total_national))}) : '
                f'{_fmt(ecart_national)} [{statut}]'
            ) if ecart_national else self.style.SUCCESS(
                f'Total national confirmé : {_fmt(int(total_national))} [OK]'
            ))
        if no_refresh:
            self.stdout.write(self.style.WARNING(
                '--no-refresh-geo : geo.Region/Departement non modifiés.'
            ))
        else:
            self.stdout.write(
                'geo rafraîchi : '
                f'{len(regions_ok)} régions, {len(depts_ok)} départements '
                "(population_source='RGPH-5 2023 (ANSD)')."
            )


def _fmt(nombre):
    return f'{nombre:,}'.replace(',', ' ')
