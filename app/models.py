from django.db import models


class Pays(models.Model):
    pays = models.CharField(max_length=255)
    capital = models.CharField(max_length=255)
    langueOfficielle = models.CharField(max_length=255)
    languesNationales = models.JSONField()
    monnaie = models.CharField(max_length=255)
    devise = models.CharField(max_length=255)
    drapeau = models.URLField(max_length=255)
    codeIso = models.CharField(max_length=255)
    indicatif = models.PositiveIntegerField()
    habitants = models.PositiveIntegerField()
    surface = models.PositiveIntegerField()
    regions = models.PositiveIntegerField()
    departments = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Pays'
        verbose_name_plural = 'Pays'

    def __str__(self):
        return self.pays


class Departements(models.Model):
    nom = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    population = models.PositiveIntegerField()
    superficie = models.PositiveIntegerField()
    arrondissements = models.JSONField()

    class Meta:
        verbose_name = 'Departement'
        verbose_name_plural = 'Departements'

    def __str__(self):
        return self.nom


class Regions(models.Model):
    nom = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    population = models.PositiveIntegerField()
    superficie = models.PositiveIntegerField()
    departments = models.JSONField()

    class Meta:
        verbose_name = 'Region'
        verbose_name_plural = 'Regions'

    def __str__(self):
        return self.nom


class Village(models.Model):
    nom = models.CharField(max_length=255)
    region = models.CharField(max_length=255)


    class Meta:
        verbose_name = 'Village'
        verbose_name_plural = 'Villages'

    def __str__(self):
        return self.nom
    
class Arrondissement(models.Model):
    nom = models.CharField(max_length=255)
    region = models.CharField(max_length=255)


    class Meta:
        verbose_name = 'Arrondissement'
        verbose_name_plural = 'Arrondissements'

    def __str__(self):
        return self.nom    

class Commune(models.Model):
    nom = models.CharField(max_length=255)
    region = models.CharField(max_length=255)


    class Meta:
        verbose_name = 'Commune'
        verbose_name_plural = 'Communes'

    def __str__(self):
        return self.nom
    
    
class Universites(models.Model):
    nom = models.CharField(max_length=255)
    logo = models.CharField(max_length=255)


    class Meta:
        verbose_name = 'Universite'
        verbose_name_plural = 'Universites'

    def __str__(self):
        return self.nom   
       


