from django.contrib import admin

from .models import Pays, Regions, Departements,Village


class PaysAdmin(admin.ModelAdmin):
    list_display = ('pays', 'capital', 'codeIso', 'habitants', 'surface')
    search_fields = ('pays', 'capital', 'codeIso')
    list_filter = ('monnaie',)


class RegionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'population', 'superficie')
    search_fields = ('nom', 'code')
    list_filter = ('superficie',)


class DepartementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'region', 'population', 'superficie')
    search_fields = ('nom', 'region__nom')
    list_filter = ('region',)

class VillageAdmin(admin.ModelAdmin):
    list_display = ('nom', 'region')
    search_fields = ('nom',)
    list_filter = ('region',)


admin.site.register(Pays, PaysAdmin)
admin.site.register(Regions, RegionAdmin)
admin.site.register(Departements, DepartementAdmin)
admin.site.register(Village, VillageAdmin)
