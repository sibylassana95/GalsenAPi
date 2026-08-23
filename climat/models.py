from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class StationClimatique(models.Model):
    """Station météo GHCN-Daily (NCEI NOAA) présente au Sénégal.

    `station_id` est l'identifiant GHCN officiel à 11 caractères
    (ex. 'SG000061641' pour Dakar-Yoff) : 2 lettres de code pays (SG),
    puis un réseau/alphabet et un numéro WMO interne. Les coordonnées et
    l'altitude proviennent de l'inventaire ghcnd-stations.txt.
    """

    station_id = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    altitude = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
    )
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['nom']
        indexes = [models.Index(fields=['nom'])]

    def __str__(self):
        return f'{self.nom} ({self.station_id})'


class ObservationMensuelle(models.Model):
    """Agrégat mensuel d'observations journalières GHCN-Daily.

    tavg/tmin/tmax sont les MOYENNES des jours documentés du mois ;
    prcp_mm est la SOMME des précipitations du mois ; nb_jours compte les
    lignes sources ayant fourni au moins une valeur exploitable. Les
    valeurs source en dixièmes (°C×10, mm×10) sont converties avant
    stockage ; un mois sans valeur mesurée reste à NULL (jamais inventé).
    """

    station = models.ForeignKey(
        StationClimatique, on_delete=models.CASCADE,
        related_name='observations',
    )
    annee = models.PositiveIntegerField()
    mois = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    tavg = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
    )
    tmin = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
    )
    tmax = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
    )
    prcp_mm = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, blank=True,
    )
    nb_jours = models.PositiveIntegerField(default=0)
    source = models.ForeignKey(
        'datasets.DataSource', on_delete=models.SET_NULL, null=True,
        blank=True, related_name='observations_climat',
    )
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-annee', '-mois']
        constraints = [
            models.UniqueConstraint(
                fields=['station', 'annee', 'mois'],
                name='uniq_observation_station_annee_mois',
            ),
        ]
        indexes = [models.Index(fields=['station', 'annee'])]

    def __str__(self):
        return f'{self.station.station_id} {self.annee}-{self.mois:02d}'
