from django.contrib import admin

from .models import (
    Link,
    LinkDefault,
    Template
)
# Register your models here.

@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_filter = ('id',)

@admin.register(LinkDefault)
class LinkDefaultsAdmin(admin.ModelAdmin):
    list_display = ('company',)


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_filter = ('type',)
    list_display = ('name', 'type',)
