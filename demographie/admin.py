from django.contrib import admin

from .models import PopulationRecord


@admin.register(PopulationRecord)
class PopulationRecordAdmin(admin.ModelAdmin):
    list_display = (
        'entity_type', 'region', 'departement', 'annee',
        'population', 'hommes', 'femmes', 'value_type', 'source',
    )
    list_filter = ('entity_type', 'value_type', 'annee')
    search_fields = ('region__nom', 'departement__nom')
    ordering = ('-annee',)
