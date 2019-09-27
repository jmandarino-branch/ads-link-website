from django.urls import path
from .views import adlinks, help_page, email_links, email_debugger, product_feeds


urlpatterns = [
    path('ads', adlinks, name='adlinks'),
    path('ads/help', help_page, name='adlinks_help'),
    path('emails', email_links, name='email_links'),
    path('email-debugger', email_debugger, name='email_debugger'),
    path('product-feeds', product_feeds, name='product_feeds')

]