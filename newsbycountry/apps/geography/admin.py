from django.contrib import admin

from apps.geography.models import Country, CountryEntityRemaps, SubRegions

# Register your models here.
admin.site.register(Country)
admin.site.register(SubRegions)
admin.site.register(CountryEntityRemaps)