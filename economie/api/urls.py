from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('economie/indicateurs', views.IndicateurEconomiqueViewSet,
                basename='indicateurs-economiques')
router.register('economie/observations', views.ObservationEconomiqueViewSet,
                basename='observations-economiques')

urlpatterns = [
    path('', include(router.urls)),
]
