from django.db.models import F
from rest_framework.filters import OrderingFilter


class NullsLastOrderingFilter(OrderingFilter):
    """OrderingFilter plaçant systématiquement les NULL en dernier.

    Nécessaire car PostgreSQL trie les NULL en premier sur les colonnes
    descendantes (contrairement à SQLite), ce qui donnerait des entités
    sans données (population inconnue, etc.) avant celles qui en ont.
    """

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        termes = []
        for terme in ordering or []:
            if terme.startswith('-'):
                termes.append(F(terme[1:]).desc(nulls_last=True))
            else:
                termes.append(F(terme).asc(nulls_last=True))
        return termes
