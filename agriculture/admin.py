from django.contrib import admin

from .models import Culture, ProductionAgricole


@admin.register(Culture)
class CultureAdmin(admin.ModelAdmin):
    list_display = ('code_faostat', 'nom')
    search_fields = ('nom', 'code_faostat')
    ordering = ('nom',)


@admin.register(ProductionAgricole)
class ProductionAgricoleAdmin(admin.ModelAdmin):
    list_display = ('culture', 'element', 'annee', 'valeur', 'flag', 'source')
    list_filter = ('element', 'annee')
    search_fields = ('culture__nom',)
    ordering = ('-annee', 'culture__nom')
