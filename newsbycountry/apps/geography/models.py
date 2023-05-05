from django.db import models

# Create your models here.
class Country(models.Model):
    alpha_2_code = models.CharField(primary_key=True, null=False, blank=False, max_length=3, default="QQ")
    alpha_3_code = models.CharField(max_length=5, null=True)
    name = models.CharField(max_length=150)
    numeric_id = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ["name"]

class SubRegions(models.Model):
    code = models.CharField(primary_key=True, null=False, blank=False, max_length=10)
    name = models.CharField(max_length=150)
    sub_region_type = models.CharField(max_length=30)
    parent_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.parent_country.name} {self.name}"
    
class CountryEntityRemaps(models.Model):
    iso_country_name = models.ForeignKey(Country, on_delete=models.CASCADE, null=True)
    remap_name = models.CharField(max_length=225, null=True)

    def __str__(self):
        f"{self.remap_name} --> {self.iso_country_name}"