from rest_framework import serializers

from datasets.models import DataQualityReport, DataSource, Dataset, DatasetVersion


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ['nom', 'slug', 'url', 'publisher', 'license_nom', 'redistribuable']


class DatasetVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetVersion
        fields = [
            'version_number', 'release_date', 'record_count',
            'checksum', 'notes', 'created_at',
        ]


class QualitySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DataQualityReport
        fields = ['valid', 'warnings', 'errors', 'duplicates', 'missing_coords', 'created_at']


class DatasetListSerializer(serializers.ModelSerializer):
    categorie_label = serializers.CharField(source='get_categorie_display', read_only=True)
    source = DataSourceSerializer(read_only=True)
    latest_version = serializers.SerializerMethodField()

    def get_latest_version(self, obj):
        latest = obj.latest_version
        if latest is None:
            return None
        return {
            'version_number': latest.version_number,
            'release_date': latest.release_date,
            'record_count': latest.record_count,
        }

    class Meta:
        model = Dataset
        fields = [
            'slug', 'titre', 'categorie', 'categorie_label', 'source',
            'latest_version', 'export_formats', 'last_refreshed',
        ]


class DatasetDetailSerializer(DatasetListSerializer):
    versions = DatasetVersionSerializer(many=True, read_only=True)
    latest_quality_report = serializers.SerializerMethodField()

    class Meta(DatasetListSerializer.Meta):
        fields = DatasetListSerializer.Meta.fields + [
            'description', 'coverage_period', 'collection_date',
            'publication_date', 'methodology', 'update_frequency',
            'versions', 'latest_quality_report',
        ]

    def get_latest_quality_report(self, obj):
        version = obj.latest_version
        if version is None:
            return None
        report = version.quality_reports.first()
        if report is None:
            return None
        return QualitySummarySerializer(report).data
