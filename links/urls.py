from django.urls import path
from .views import adlinks, help_page


urlpatterns = [
    path('', adlinks, name='adlinks'),
    path('help', help_page, name='adlinks_help')
]