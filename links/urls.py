from django.urls import path
from .views import index, simple_upload


urlpatterns = [
    path('', simple_upload, name='simple_upload'),
]