from django.db import models


class DataSource(models.Model):
    nom = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    url = models.URLField(max_length=500)
    publisher = models.CharField(max_length=200, blank=True, default='')
    description = models.TextField(blank=True, default='')
    license_nom = models.CharField(max_length=100)
    license_url = models.URLField(max_length=500, blank=True, default='')
    redistribuable = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom']
        indexes = [models.Index(fields=['nom'])]

    def __str__(self):
        return self.nom


class Dataset(models.Model):
    CATEGORIE_CHOICES = [
        ('geographie', 'Géographie'),
        ('demographie', 'Démographie'),
        ('education', 'Éducation'),
        ('sante', 'Santé'),
        ('agriculture', 'Agriculture'),
        ('climat', 'Climat'),
        ('economie', 'Économie'),
        ('transport', 'Transport'),
        ('tourisme', 'Tourisme'),
        ('culture', 'Culture'),
        ('energie', 'Énergie'),
        ('autre', 'Autre'),
    ]

    titre = models.CharField(max_length=250)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField()
    categorie = models.CharField(max_length=30, choices=CATEGORIE_CHOICES)
    source = models.ForeignKey(DataSource, on_delete=models.PROTECT, related_name='datasets')
    coverage_period = models.CharField(max_length=50, blank=True, default='')
    collection_date = models.DateField(null=True, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    last_refreshed = models.DateTimeField(auto_now=True)
    methodology = models.TextField(blank=True, default='')
    update_frequency = models.CharField(max_length=50, blank=True, default='')
    export_formats = models.JSONField(default=list, blank=True)
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ['titre']
        indexes = [models.Index(fields=['categorie'])]

    def __str__(self):
        return self.titre

    @property
    def latest_version(self):
        return self.versions.order_by('-release_date', '-created_at').first()


class DatasetVersion(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=20, default='1.0.0')
    release_date = models.DateField(null=True, blank=True)
    record_count = models.PositiveIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-release_date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['dataset', 'version_number'],
                name='uniq_dataset_version_number',
            ),
        ]

    def __str__(self):
        return f'{self.dataset.slug} v{self.version_number}'


class DataQualityReport(models.Model):
    version = models.ForeignKey(
        DatasetVersion, on_delete=models.CASCADE, related_name='quality_reports'
    )
    valid = models.PositiveIntegerField(default=0)
    warnings = models.PositiveIntegerField(default=0)
    errors = models.PositiveIntegerField(default=0)
    duplicates = models.PositiveIntegerField(default=0)
    missing_coords = models.PositiveIntegerField(default=0)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Rapport {self.version} ({self.created_at:%Y-%m-%d %H:%M})'
