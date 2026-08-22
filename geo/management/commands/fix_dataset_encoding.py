import json

from django.core.management.base import BaseCommand

from geo.ingest import BACKUP_DIR, DATASET_DIR
from geo.utils import looks_mojibake, repair_mojibake

TARGET_FILES = [
    'senegal',
    'regions',
    'departments',
    'arrondissement',
    'commune',
    'village',
    'universite_ecole_formation',
]


def transform_json(value, stats):
    """Répare récursivement toutes les chaînes d'une structure JSON."""
    if isinstance(value, str):
        repaired = repair_mojibake(value)
        if repaired is not None:
            stats['repaires'] += 1
            return repaired
        if looks_mojibake(value):
            stats['non_repaires'] += 1
        return value
    if isinstance(value, list):
        return [transform_json(item, stats) for item in value]
    if isinstance(value, dict):
        return {key: transform_json(item, stats) for key, item in value.items()}
    return value


def repair_json_bytes(raw: bytes):
    """Retourne (nouvelles_lettres|None, stats) pour un fichier JSON donné."""
    obj = json.loads(raw.decode('utf-8'))
    stats = {'repaires': 0, 'non_repaires': 0}
    new_obj = transform_json(obj, stats)
    if stats['repaires'] == 0:
        return None, stats
    content = json.dumps(new_obj, ensure_ascii=False, indent=2) + '\n'
    return content.encode('utf-8'), stats


class Command(BaseCommand):
    help = "Répare le mojibake des dataset/*.json (backup obligatoire avant écriture)."

    def handle(self, *args, **options):
        total = 0
        for name in TARGET_FILES:
            path = DATASET_DIR / f'{name}.json'
            if not path.exists():
                self.stdout.write(self.style.WARNING(f"{path.name}: absent, ignoré"))
                continue
            raw = path.read_bytes()
            new_content, stats = repair_json_bytes(raw)
            if new_content is None:
                detail = ''
                if stats['non_repaires']:
                    detail = f" ({stats['non_repaires']} chaîne(s) mojibake non réparable(s))"
                self.stdout.write(f"{path.name}: 0 réparation{detail}")
                continue
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            backup = BACKUP_DIR / f'{name}.json.bak'
            backup.write_bytes(raw)
            path.write_bytes(new_content)
            total += stats['repaires']
            self.stdout.write(self.style.SUCCESS(
                f"{path.name}: {stats['repaires']} chaîne(s) réparée(s), "
                f"backup -> {backup}"
            ))
        self.stdout.write(self.style.SUCCESS(f"Total réparations: {total}"))
