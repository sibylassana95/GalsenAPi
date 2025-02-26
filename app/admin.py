from django.contrib import admin

from .models import Pays, Regions, Departements,Village,Arrondissement,Commune,Universites


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

class ArrondissementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'region')
    search_fields = ('nom',)
    list_filter = ('region',)
    
class CommuneAdmin(admin.ModelAdmin):
    list_display = ('nom', 'region')
    search_fields = ('nom',)
    list_filter = ('region',)
    
class UniversiteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'logo')
    search_fields = ('nom',)
    list_filter = ('nom',)
    
            
admin.site.register(Pays, PaysAdmin)
admin.site.register(Regions, RegionAdmin)
admin.site.register(Departements, DepartementAdmin)
admin.site.register(Village, VillageAdmin)
admin.site.register(Arrondissement, ArrondissementAdmin)
admin.site.register(Commune, CommuneAdmin)
admin.site.register(Universites, UniversiteAdmin)


