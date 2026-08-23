from django.db import models


class IndicateurEconomique(models.Model):
    """Indicateur macroéconomique World Bank Indicators pour le Sénégal.

    `nom` est le libellé français court du curateur (economie/indicators.py) ;
    `nom_officiel` est le nom anglais officiel renvoyé par la méta de l'API
    (champ indicator.value). Les noms officiels EN proviennent donc de l'API,
    pas d'une traduction locale.
    """

    CATEGORIE_CHOICES = [
        ('pib', 'PIB'),
        ('prix', 'Prix & inflation'),
        ('commerce', 'Commerce'),
        ('emploi', 'Emploi'),
        ('dette', 'Dette & finance publique'),
        ('secteurs', 'Structure économique'),
    ]

    code = models.CharField(max_length=30, unique=True)
    nom = models.CharField(max_length=250)
    nom_officiel = models.CharField(max_length=250, blank=True, default='')
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    unite = models.CharField(max_length=30, blank=True, default='')
    decimal = models.CharField(max_length=3, blank=True, default='')
    source = models.ForeignKey(
        'datasets.DataSource', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='indicateurs_economiques',
    )
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['categorie', 'code']
        indexes = [models.Index(fields=['categorie'])]

    def __str__(self):
        return f'{self.nom} ({self.code})'


class ObservationEconomique(models.Model):
    """Valeur annuelle d'un indicateur économique au Sénégal.

    max_digits=24 : les PIB en US$ courants (~3,7e10) et PPA dépassent le
    Decimal(16) classique. Les observations sans valeur (null côté API) ne
    sont pas importées ; le champ reste nullable par prudence.
    """

    indicateur = models.ForeignKey(
        IndicateurEconomique, on_delete=models.CASCADE,
        related_name='observations',
    )
    annee = models.PositiveIntegerField()
    valeur = models.DecimalField(
        max_digits=24, decimal_places=6, null=True, blank=True
    )

    class Meta:
        ordering = ['-annee']
        constraints = [
            models.UniqueConstraint(
                fields=['indicateur', 'annee'],
                name='uniq_observation_indicateur_annee',
            ),
        ]
        indexes = [models.Index(fields=['annee'])]

    def __str__(self):
        return f'{self.indicateur.code} {self.annee} : {self.valeur}'
