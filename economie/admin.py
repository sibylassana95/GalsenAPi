from django.contrib import admin

from .models import IndicateurEconomique, ObservationEconomique


@admin.register(IndicateurEconomique)
class IndicateurEconomiqueAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'categorie', 'unite', 'source')
    list_filter = ('categorie',)
    search_fields = ('code', 'nom', 'nom_officiel')
    ordering = ('categorie', 'code')


@admin.register(ObservationEconomique)
class ObservationEconomiqueAdmin(admin.ModelAdmin):
    list_display = ('indicateur', 'annee', 'valeur')
    list_filter = ('annee',)
    search_fields = ('indicateur__code', 'indicateur__nom')
    ordering = ('-annee', 'indicateur__code')
