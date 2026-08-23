from django.db import models


class Pays(models.Model):
    nom = models.CharField(max_length=100, default='Sénégal')
    code_iso2 = models.CharField(max_length=2, unique=True, default='SN')
    capitale = models.CharField(max_length=100, blank=True, default='')
    indicatif = models.PositiveIntegerField(null=True, blank=True)
    monnaie = models.CharField(max_length=50, blank=True, default='')
    devise = models.CharField(max_length=150, blank=True, default='')
    population = models.PositiveIntegerField(null=True, blank=True)
    superficie_km2 = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    class Meta:
        ordering = ['nom']
        indexes = [models.Index(fields=['nom'])]

    def __str__(self):
        return self.nom


class GeoLevelMixin(models.Model):
    geometry = models.JSONField(null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True


class Region(GeoLevelMixin):
    pays = models.ForeignKey(Pays, on_delete=models.PROTECT, related_name='regions')
    pcode = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    code_court = models.CharField(max_length=10, null=True, blank=True)
    chef_lieu = models.CharField(max_length=100, null=True, blank=True)
    population = models.PositiveIntegerField(null=True, blank=True)
    superficie_km2 = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    class Meta:
        ordering = ['nom']
        indexes = [models.Index(fields=['nom'])]

    def __str__(self):
        return self.nom


class Departement(GeoLevelMixin):
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='departements')
    pcode = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    population = models.PositiveIntegerField(null=True, blank=True)
    superficie_km2 = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    class Meta:
        ordering = ['nom']
        indexes = [models.Index(fields=['nom'])]
        constraints = [
            models.UniqueConstraint(fields=['region', 'nom'], name='uniq_departement_region_nom'),
        ]

    def __str__(self):
        return self.nom


class Arrondissement(GeoLevelMixin):
    departement = models.ForeignKey(
        Departement, on_delete=models.PROTECT, related_name='arrondissements'
    )
    pcode = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)

    class Meta:
        ordering = ['nom']
        indexes = [models.Index(fields=['nom'])]
        constraints = [
            models.UniqueConstraint(fields=['departement', 'nom'], name='uniq_arrondissement_departement_nom'),
        ]

    def __str__(self):
        return self.nom


class Commune(GeoLevelMixin):
    TYPE_CHOICES = [
        ('commune', 'Commune'),
        ('communaute_rurale', 'Communauté rurale'),
        ('autre', 'Autre'),
    ]

    departement = models.ForeignKey(
        Departement, on_delete=models.PROTECT, related_name='communes'
    )
    arrondissement = models.ForeignKey(
        Arrondissement, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='communes'
    )
    nom = models.CharField(max_length=150)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='commune')
    population = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['nom']
        indexes = [models.Index(fields=['nom'])]
        constraints = [
            models.UniqueConstraint(fields=['departement', 'nom'], name='uniq_commune_departement_nom'),
        ]

    def __str__(self):
        return self.nom


class Village(GeoLevelMixin):
    commune = models.ForeignKey(
        Commune, on_delete=models.SET_NULL, null=True, blank=True, related_name='villages'
    )
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='villages')
    nom = models.CharField(max_length=200)
    population = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['nom']
        indexes = [models.Index(fields=['nom'])]
        constraints = [
            models.UniqueConstraint(fields=['region', 'nom'], name='uniq_village_region_nom'),
        ]

    def __str__(self):
        return self.nom
