from django.urls import path

from . import views

urlpatterns = [

    path('paysapi/', views.pays_view, name='paysapi'),
    path('departementapi/', views.departement_view, name='departementapi'),
    path('regionapi/', views.region_view, name='regionapi'),


    path('api/pays/', views.PaysList.as_view(), name='pays_list'),
    path('api/departements/', views.DepartementsList.as_view(), name='departements_list'),
    path('api/departements/<int:pk>/', views.DepartementsDetail.as_view(), name='departements_detail'),
    path('api/regions/', views.RegionsList.as_view(), name='regions_list'),
    path('api/regions/<int:pk>/', views.RegionsDetail.as_view(), name='regions_detail'),
]
