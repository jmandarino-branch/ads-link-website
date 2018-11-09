from django.contrib import admin

from .models import (
    Link,
    LinkDefaults
)
# Register your models here.

@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_filter = ('id',)

@admin.register(LinkDefaults)
class LinkDefaultsAdmin(admin.ModelAdmin):
    list_filter = ('id',)
