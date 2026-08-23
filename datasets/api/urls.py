from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('datasets', views.DatasetViewSet, basename='datasets')

urlpatterns = router.urls
