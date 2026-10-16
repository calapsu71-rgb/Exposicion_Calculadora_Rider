from django.urls import path
from .views import calcular_view, resultado_view

urlpatterns = [
    path('', calcular_view, name='index'),
    path('resultado/', resultado_view, name='resultado'),
]