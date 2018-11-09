from django.contrib import admin

from .models import (
    User,
    Company,
)
# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_filter = ('id',)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_filter = ('name',)
