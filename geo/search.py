from django.db.models import Q
from django.urls import reverse

from app.models import Universites
from datasets.models import Dataset
from geo.models import Arrondissement, Commune, Departement, Region, Village

TYPE_LABELS = {
    'region': 'Région',
    'departement': 'Département',
    'arrondissement': 'Arrondissement',
    'commune': 'Commune',
    'village': 'Village',
    'universite': 'Université',
    'dataset': 'Dataset',
}

DEFAULT_LIMIT = 20
MAX_LIMIT = 50


class SearchValidationError(ValueError):
    def __init__(self, detail):
        super().__init__(detail)
        self.detail = detail


def parse_types(raw):
    if raw is None or raw.strip() == '':
        return list(TYPE_LABELS)
    types = [item.strip().lower() for item in raw.split(',') if item.strip()]
    invalid = [t for t in types if t not in TYPE_LABELS]
    if invalid:
        raise SearchValidationError(
            "Types invalides : {}. Types valides : {}.".format(
                ', '.join(invalid), ', '.join(TYPE_LABELS)
            )
        )
    seen = set()
    return [t for t in types if not (t in seen or seen.add(t))]


def parse_limit(raw):
    if raw is None or raw.strip() == '':
        return DEFAULT_LIMIT
    try:
        limit = int(raw)
    except (TypeError, ValueError):
        raise SearchValidationError("Paramètre 'limit' invalide : entier attendu.")
    if limit < 1:
        raise SearchValidationError("Paramètre 'limit' invalide : minimum 1.")
    return min(limit, MAX_LIMIT)


def _score(nom, term):
    lowered = nom.casefold()
    if lowered == term:
        return 0
    if lowered.startswith(term):
        return 1
    return 2


def _entry(type_, nom, *, pcode=None, id_=None, parent=None, url=None, extra=None):
    return {
        'type': type_,
        'type_label': TYPE_LABELS[type_],
        'pcode': pcode,
        'id': id_,
        'nom': nom,
        'parent': parent,
        'url': url,
        'extra': extra or {},
    }


def _parent(type_, nom=None, pcode=None):
    return {'type': type_, 'nom': nom, 'pcode': pcode}


def _collect(term, types, limit):
    results = []

    if 'region' in types:
        rows = Region.objects.filter(nom__icontains=term).values(
            'pcode', 'nom', 'code_court', 'chef_lieu', 'population', 'superficie_km2'
        )[:limit]
        for row in rows:
            superficie = row['superficie_km2']
            results.append(_entry(
                'region', row['nom'], pcode=row['pcode'],
                url=reverse('regions-detail', kwargs={'pcode': row['pcode']}),
                extra={
                    'population': row['population'],
                    'superficie_km2': float(superficie) if superficie is not None else None,
                    'code_court': row['code_court'],
                    'chef_lieu': row['chef_lieu'],
                },
            ))

    if 'departement' in types:
        rows = (
            Departement.objects.select_related('region')
            .filter(nom__icontains=term)
            .values('pcode', 'nom', 'region__pcode', 'region__nom')[:limit]
        )
        for row in rows:
            results.append(_entry(
                'departement', row['nom'], pcode=row['pcode'],
                parent=_parent('region', row['region__nom'], row['region__pcode']),
                url=reverse('departements-detail', kwargs={'pcode': row['pcode']}),
            ))

    if 'arrondissement' in types:
        rows = (
            Arrondissement.objects.select_related('departement')
            .filter(nom__icontains=term)
            .values('pcode', 'nom', 'departement__pcode', 'departement__nom')[:limit]
        )
        for row in rows:
            results.append(_entry(
                'arrondissement', row['nom'], pcode=row['pcode'],
                parent=_parent(
                    'departement', row['departement__nom'], row['departement__pcode']
                ),
                url=reverse('arrondissements-detail', kwargs={'pcode': row['pcode']}),
            ))

    if 'commune' in types:
        rows = (
            Commune.objects.select_related('departement')
            .filter(nom__icontains=term)
            .values('id', 'nom', 'departement__pcode', 'departement__nom')[:limit]
        )
        for row in rows:
            results.append(_entry(
                'commune', row['nom'], id_=row['id'],
                parent=_parent(
                    'departement', row['departement__nom'], row['departement__pcode']
                ),
                url=reverse('communes-detail', kwargs={'pk': row['id']}),
            ))

    if 'village' in types:
        rows = (
            Village.objects.select_related('region')
            .filter(nom__icontains=term)
            .values('id', 'nom', 'region__pcode', 'region__nom')[:limit]
        )
        for row in rows:
            results.append(_entry(
                'village', row['nom'], id_=row['id'],
                parent=_parent('region', row['region__nom'], row['region__pcode']),
                url=reverse('villages-detail', kwargs={'pk': row['id']}),
            ))

    if 'universite' in types:
        rows = Universites.objects.filter(nom__icontains=term)[:limit]
        for univ in rows:
            results.append(_entry(
                'universite', univ.nom, id_=univ.pk,
                extra={'logo': univ.logo},
            ))

    if 'dataset' in types:
        rows = Dataset.objects.filter(is_public=True).filter(
            Q(titre__icontains=term) | Q(slug__icontains=term) | Q(description__icontains=term)
        ).values('slug', 'titre', 'categorie')[:limit]
        for row in rows:
            results.append(_entry(
                'dataset', row['titre'],
                url=reverse('datasets-detail', kwargs={'slug': row['slug']}),
                extra={'slug': row['slug'], 'categorie': row['categorie']},
            ))

    return results


def search(raw_term, types=None, limit=DEFAULT_LIMIT):
    term = raw_term.strip().casefold()
    results = _collect(raw_term.strip(), types, limit)
    results.sort(key=lambda entry: (_score(entry['nom'], term), entry['nom'].casefold()))
    return results
