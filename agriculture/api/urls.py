from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('agriculture/cultures', views.CultureViewSet, basename='cultures')
router.register('agriculture/production', views.ProductionAgricoleViewSet,
                basename='production-agricole')

urlpatterns = [
    path('', include(router.urls)),
]
