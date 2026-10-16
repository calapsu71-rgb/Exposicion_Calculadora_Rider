from django.urls import path
from .views import index, resultado

urlpatterns = [
    path('', index, name='index'),
    path('resultado/', resultado, name='resultado'),
]