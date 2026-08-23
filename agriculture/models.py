from django.db import models


class Culture(models.Model):
    """Culture ou produit FAOSTAT (QCL), identifié par son code item FAO."""

    code_faostat = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=250)

    class Meta:
        ordering = ['nom']
        indexes = [models.Index(fields=['nom'])]

    def __str__(self):
        return f'{self.nom} ({self.code_faostat})'


class ProductionAgricole(models.Model):
    """Valeur annuelle FAOSTAT pour une culture au Sénégal (production,
    superficie récoltée ou rendement)."""

    ELEMENT_CHOICES = [
        ('production_tonnes', 'Production (tonnes)'),
        ('superficie_recoltee_ha', 'Superficie récoltée (ha)'),
        ('rendement_hg_ha', 'Rendement (hg/ha)'),
    ]

    culture = models.ForeignKey(
        Culture, on_delete=models.CASCADE, related_name='productions'
    )
    annee = models.PositiveIntegerField()
    element = models.CharField(max_length=30, choices=ELEMENT_CHOICES)
    valeur = models.DecimalField(
        max_digits=16, decimal_places=4, null=True, blank=True
    )
    flag = models.CharField(max_length=3, blank=True, default='')
    source = models.ForeignKey(
        'datasets.DataSource', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='productions_agricoles',
    )
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-annee', 'culture__nom']
        constraints = [
            models.UniqueConstraint(
                fields=['culture', 'annee', 'element'],
                name='uniq_production_culture_annee_element',
            ),
        ]
        indexes = [models.Index(fields=['annee'])]

    def __str__(self):
        return f'{self.culture} — {self.element} {self.annee} : {self.valeur}'
