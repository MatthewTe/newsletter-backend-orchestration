from django.contrib import admin

from apps.geography.models import Country, SubRegions

# Register your models here.
admin.site.register(Country)
admin.site.register(SubRegions)