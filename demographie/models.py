from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


def _condition_region():
    return Q(entity_type='region', region__isnull=False, departement__isnull=True)


def _condition_departement():
    return Q(entity_type='departement', departement__isnull=False, region__isnull=False)


class PopulationRecord(models.Model):
    """Effectif de population pour une entité administrative (RGPH-5 2023, etc.)."""

    ENTITY_TYPE_CHOICES = [
        ('region', 'Région'),
        ('departement', 'Département'),
    ]
    VALUE_TYPE_CHOICES = [
        ('officielle', 'Officielle'),
        ('estimee', 'Estimée'),
    ]

    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPE_CHOICES)
    region = models.ForeignKey(
        'geo.Region', on_delete=models.PROTECT, null=True, blank=True,
        related_name='population_records',
    )
    departement = models.ForeignKey(
        'geo.Departement', on_delete=models.PROTECT, null=True, blank=True,
        related_name='population_records',
    )
    annee = models.PositiveIntegerField()
    population = models.PositiveIntegerField()
    hommes = models.PositiveIntegerField(null=True, blank=True)
    femmes = models.PositiveIntegerField(null=True, blank=True)
    value_type = models.CharField(
        max_length=12, choices=VALUE_TYPE_CHOICES, default='officielle'
    )
    source = models.ForeignKey(
        'datasets.DataSource', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='population_records',
    )
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-annee']
        constraints = [
            # Deux contraintes conditionnelles plutôt qu'une seule sur
            # (entity_type, region, departement, annee) : dans un index unique
            # composite, une colonne NULL rend les clés distinctes (SQL standard),
            # ce qui neutraliserait l'unicité des enregistrements 'region'
            # (departement_id NULL). Chaque branche ne porte donc que des
            # colonnes renseignées.
            models.UniqueConstraint(
                fields=['region', 'annee'],
                condition=_condition_region(),
                name='uniq_population_region_annee',
            ),
            models.UniqueConstraint(
                fields=['departement', 'annee'],
                condition=_condition_departement(),
                name='uniq_population_departement_annee',
            ),
        ]
        indexes = [models.Index(fields=['entity_type', 'annee'])]

    def __str__(self):
        entite = self.region if self.entity_type == 'region' else self.departement
        return f'{entite} ({self.annee}) : {self.population}'

    def clean(self):
        if self.entity_type == 'region':
            if self.region is None or self.departement is not None:
                raise ValidationError(
                    "Un enregistrement 'region' exige region renseignée et "
                    "departement vide."
                )
        elif self.entity_type == 'departement':
            if self.departement is None or self.region is None:
                raise ValidationError(
                    "Un enregistrement 'departement' exige departement et sa "
                    "region parente renseignés."
                )
        else:
            raise ValidationError(f"entity_type inconnu : {self.entity_type}")
