
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from rest_framework import permissions

from . import frontend_views


class ApiV1SchemaGenerator(OpenAPISchemaGenerator):
    """Ne documente que l'API moderne /api/v1/ (les routes legacy restent servies mais hors doc)."""

    def get_endpoints(self, request=None):
        endpoints = super().get_endpoints(request)
        return {
            path: item
            for path, item in endpoints.items()
            if path.startswith('/api/v1')
        }

schema_view = get_schema_view(
    openapi.Info(
        title="GalsenApi",
        default_version='v2',
        description="GalsenApi est une API qui vous permet de manipuler facilement des données sur le Sénégal.",
        terms_of_service="https://github.com/sibylassana95/GalsenAPi/blob/main/Licence.md",
        contact=openapi.Contact(email="sibyamara95@gmail.com"),
        license=openapi.License(name="Mit"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    generator_class=ApiV1SchemaGenerator,
)
urlpatterns = [
    path('admin', admin.site.urls),
    path('', frontend_views.home_view, name='home'),
    path('donnees/', frontend_views.donnees_view, name='donnees'),
    path('donnees/geographie/', frontend_views.geographie_view, name='geographie'),
    path('region/', frontend_views.regions_liste_view, name='region'),
    path('regions/<str:pcode>/', frontend_views.region_detail_view, name='region-detail'),
    path('departements/<str:pcode>/', frontend_views.departement_detail_view, name='departement-detail'),
    path('demographie/', frontend_views.demographie_dashboard, name='dashboard-demographie'),
    path('agriculture/', frontend_views.agriculture_dashboard, name='dashboard-agriculture'),
    path('climat/', frontend_views.climat_dashboard, name='dashboard-climat'),
    path('economie/', frontend_views.economie_dashboard, name='dashboard-economie'),
    path('education/', frontend_views.education_page, name='education'),
    path('developers/', frontend_views.developers_page, name='developers'),
    path('', include('app.urls')),
    path('api/v1/', include('geo.api.urls')),
    path('api/v1/', include('datasets.api.urls')),
    path('api/v1/', include('demographie.api.urls')),
    path('api/v1/', include('agriculture.api.urls')),
    path('api/v1/', include('economie.api.urls')),
    path('api/v1/', include('climat.api.urls')),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='docs'),
    path('docs', schema_view.with_ui('swagger', cache_timeout=0)),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
    path('redoc', schema_view.with_ui('redoc', cache_timeout=0)),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
