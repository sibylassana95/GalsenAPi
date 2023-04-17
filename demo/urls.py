from django.urls import path

from . import views

urlpatterns = [
    path('', views.pays_view, name='home'),
    path('regions/', views.regions_view, name='region'),
    path('departments', views.departments_view, name='departement')

]
