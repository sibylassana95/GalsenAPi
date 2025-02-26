from django.urls import path

from . import views

urlpatterns = [

    path('', views.pays_view, name='home'),
    path('departement/', views.departement_view, name='departement'),
    path('region/', views.region_view, name='region'),
    path('village/', views.village_view, name='village'),
    path('arrondissement/', views.arrondissement_view, name='arrondissement'),
    path('commune/', views.commune_view, name='commune'),
    path('universite/', views.universite_view, name='universite'),


    path('api/pays/', views.PaysList.as_view(), name='pays_list'),
    path('api/departements/', views.DepartementsList.as_view(), name='departements_list'),
    path('api/departements/<int:pk>/', views.DepartementsDetail.as_view(), name='departements_detail'),
    path('api/regions/', views.RegionsList.as_view(), name='regions_list'),
    path('api/regions/<int:pk>/', views.RegionsDetail.as_view(), name='regions_detail'),
    path('api/villages/', views.VillageList.as_view(), name='villages_list'),
    path('api/villages/<int:pk>/', views.VillageDetail.as_view(), name='villages_detail'),
    path('api/arrondissements/', views.ArrondissementList.as_view(), name='arrondissements_list'),
    path('api/arrondissements/<int:pk>/', views.ArrondissementDetail.as_view(), name='arrondissements_detail'),
    path('api/communes/', views.CommuneList.as_view(), name='communes_list'),
    path('api/communes/<int:pk>/', views.CommuneDetail.as_view(), name='communes_detail'),
    path('api/universites/', views.UniversitesList.as_view(), name='universites_list'),
    path('api/universites/<int:pk>/', views.UniversitesDetail.as_view(), name='universites_detail'),
]
