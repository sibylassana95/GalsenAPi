from django.contrib import admin

from .models import DataQualityReport, DataSource, Dataset, DatasetVersion


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'slug', 'publisher', 'license_nom', 'redistribuable')
    search_fields = ('nom', 'slug', 'publisher')
    list_filter = ('redistribuable',)


class DatasetVersionInline(admin.TabularInline):
    model = DatasetVersion
    extra = 0


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = (
        'titre', 'slug', 'categorie', 'source', 'coverage_period',
        'is_public', 'last_refreshed',
    )
    search_fields = ('titre', 'slug', 'description')
    list_filter = ('categorie', 'source', 'is_public')
    inlines = [DatasetVersionInline]


@admin.register(DatasetVersion)
class DatasetVersionAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'version_number', 'release_date', 'record_count', 'created_at')
    search_fields = ('dataset__titre', 'dataset__slug', 'version_number')
    list_filter = ('dataset__categorie',)


@admin.register(DataQualityReport)
class DataQualityReportAdmin(admin.ModelAdmin):
    list_display = (
        'version', 'valid', 'warnings', 'errors', 'duplicates', 'missing_coords', 'created_at',
    )
    list_filter = ('version__dataset__categorie',)
