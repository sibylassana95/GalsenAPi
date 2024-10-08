
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf.urls import handler404
from rest_framework_swagger.views import get_swagger_view
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings

schema_view = get_schema_view(
    openapi.Info(
        title="GalsenApi",
        default_version='v1',
        description="GalsenApi est une API qui vous permet de manipuler facilement des données sur le Sénégal.",
        terms_of_service="https://github.com/sibylassana95/GalsenAPi/blob/main/Licence.md",
        contact=openapi.Contact(email="sibyamara95@gmail.com"),
        license=openapi.License(name="Mit"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    path('admin', admin.site.urls),
    path('', include('app.urls')),
    path('docs', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
handler404="app.views.error_404"
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)