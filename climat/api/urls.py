from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('climat/stations', views.StationClimatiqueViewSet,
                basename='stations-climatiques')
router.register('climat/observations', views.ObservationMensuelleViewSet,
                basename='observations-climatiques')

urlpatterns = [
    path('', include(router.urls)),
]
