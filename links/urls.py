from django.urls import path
from .views import adlinks, help_page, email_links, email_debugger, link_updater, product_feeds, product_feeds_help


urlpatterns = [
    path('ads', adlinks, name='adlinks'),
    path('ads/help', help_page, name='adlinks_help'),
    path('emails', email_links, name='email_links'),
    path('email-debugger', email_debugger, name='email_debugger'),
    path('product-feeds', product_feeds, name='product_feeds'),
    path('link-updater', link_updater, name='link_updater'),
    path('product-feeds/help', product_feeds_help, name='product_feeds_help'),

]