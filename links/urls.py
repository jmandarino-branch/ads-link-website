from django.urls import path
from .views import adlinks


urlpatterns = [
    path('', adlinks, name='adlinks'),
]