from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from links.models import LinkDefaults

from .models import (
    User,
    Company,
)


class LinkDefaultsInline(admin.TabularInline):
    model = LinkDefaults

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_filter = ('name',)
    inlines = [LinkDefaultsInline]


class MyUserAdmin(UserAdmin):
    model = User

    fieldsets = UserAdmin.fieldsets + (
            (None, {'fields': ('company',)}),
    )


admin.site.register(User, MyUserAdmin)
