
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

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
)
urlpatterns = [
    path('admin', admin.site.urls),
    path('', include('app.urls')),
    path('docs', schema_view.with_ui('swagger', cache_timeout=0), name='docs'),
    path('redoc', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)