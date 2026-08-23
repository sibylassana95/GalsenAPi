from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('regions', views.RegionViewSet, basename='regions')
router.register('departements', views.DepartementViewSet, basename='departements')
router.register('arrondissements', views.ArrondissementViewSet, basename='arrondissements')
router.register('communes', views.CommuneViewSet, basename='communes')
router.register('villages', views.VillageViewSet, basename='villages')

urlpatterns = [
    path('search/', views.SearchView.as_view(), name='search'),
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
    path('statistics/regions/<str:pcode>/', views.RegionStatisticsView.as_view(),
         name='statistics-region'),
    path('pays/', views.PaysDetailView.as_view(), name='pays-detail'),
]

urlpatterns += router.urls
