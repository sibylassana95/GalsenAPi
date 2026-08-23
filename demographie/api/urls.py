from django.urls import path

from . import views

urlpatterns = [
    path('demographie/population/', views.PopulationListView.as_view(),
         name='demographie-population'),
]
