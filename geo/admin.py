from django.contrib import admin

from .models import Arrondissement, Commune, Departement, Pays, Region, Village


@admin.register(Pays)
class PaysAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_iso2', 'capitale', 'monnaie', 'population')
    search_fields = ('nom', 'code_iso2')


class DepartementInline(admin.TabularInline):
    model = Departement
    extra = 0


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pcode', 'code_court', 'chef_lieu', 'population', 'latitude', 'longitude')
    search_fields = ('nom', 'pcode', 'code_court')
    list_filter = ('pays',)
    inlines = [DepartementInline]


@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pcode', 'region', 'latitude', 'longitude')
    search_fields = ('nom', 'pcode')
    list_filter = ('region',)


@admin.register(Arrondissement)
class ArrondissementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pcode', 'departement', 'latitude', 'longitude')
    search_fields = ('nom', 'pcode')
    list_filter = ('departement__region',)


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ('nom', 'departement', 'arrondissement', 'type', 'latitude', 'longitude')
    search_fields = ('nom',)
    list_filter = ('type', 'departement__region')


@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ('nom', 'region', 'commune', 'latitude', 'longitude')
    search_fields = ('nom',)
    list_filter = ('region',)
