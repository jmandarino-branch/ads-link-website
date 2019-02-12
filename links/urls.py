from django.urls import path
from .views import adlinks, help_page, email_links


urlpatterns = [
    path('ads', adlinks, name='adlinks'),
    path('ads/help', help_page, name='adlinks_help'),
    path('emails', email_links, name='email_links')

]