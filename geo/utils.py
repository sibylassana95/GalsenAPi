import re
import unicodedata

MOJIBAKE_MARKERS = (chr(0xC3), chr(0xC2), chr(0x1F8), chr(0xFFFD))


def slug_nom(valeur: str) -> str:
    """Slug insensible à la casse et aux accents pour le matching de noms."""
    texte = unicodedata.normalize('NFKD', valeur or '')
    texte = texte.encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+', '-', texte.lower()).strip('-')


def looks_mojibake(texte: str) -> bool:
    """Détecte les marqueurs de mojibake (séquences latin-1/cp1252 mal décodées)."""
    if not texte:
        return False
    if any(marker in texte for marker in MOJIBAKE_MARKERS):
        return True
    return any('\x80' <= char <= '\x9f' for char in texte)


def repair_mojibake(texte):
    """Répare un mojibake par round-trip latin-1/cp1252 -> utf-8.

    Retourne la chaîne réparée, ou None si rien à réparer / non réparable.
    """
    if not texte or not isinstance(texte, str) or not looks_mojibake(texte):
        return None
    for codec in ('latin-1', 'cp1252'):
        try:
            repaired = texte.encode(codec).decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if not looks_mojibake(repaired):
            return repaired
    return None

