from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from links.models import LinkDefault

from .models import (
    User,
    Company,
)

from links.models import Template


class LinkDefaultsInline(admin.TabularInline):
    model = LinkDefault

class TemplateInline(admin.TabularInline):
    model = Company.templates.through

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_filter = ('name',)
    inlines = [LinkDefaultsInline, TemplateInline]



class MyUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
            (None, {'fields': ('company',)}),
    )


admin.site.register(User, MyUserAdmin)
