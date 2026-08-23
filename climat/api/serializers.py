from rest_framework import serializers

from climat.models import ObservationMensuelle, StationClimatique


class StationClimatiqueSerializer(serializers.ModelSerializer):
    nb_observations = serializers.IntegerField(read_only=True)

    class Meta:
        model = StationClimatique
        fields = [
            'station_id', 'nom', 'latitude', 'longitude', 'altitude',
            'nb_observations',
        ]


class ObservationMensuelleSerializer(serializers.ModelSerializer):
    station = serializers.CharField(
        source='station.station_id', read_only=True,
    )
    station_nom = serializers.CharField(
        source='station.nom', read_only=True,
    )

    class Meta:
        model = ObservationMensuelle
        fields = [
            'id', 'station', 'station_nom', 'annee', 'mois',
            'tavg', 'tmin', 'tmax', 'prcp_mm', 'nb_jours',
        ]
