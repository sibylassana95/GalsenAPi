from django.contrib import admin

from .models import ObservationMensuelle, StationClimatique


@admin.register(StationClimatique)
class StationClimatiqueAdmin(admin.ModelAdmin):
    list_display = ('station_id', 'nom', 'latitude', 'longitude', 'altitude')
    search_fields = ('station_id', 'nom')
    ordering = ('nom',)


@admin.register(ObservationMensuelle)
class ObservationMensuelleAdmin(admin.ModelAdmin):
    list_display = ('station', 'annee', 'mois', 'tavg', 'tmin', 'tmax',
                    'prcp_mm', 'nb_jours')
    list_filter = ('annee',)
    search_fields = ('station__station_id', 'station__nom')
    ordering = ('-annee', '-mois', 'station__station_id')
