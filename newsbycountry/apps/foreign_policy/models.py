from django.db import models

from apps.people.models import People
from apps.geography.models import Country

class ArticleLinks(models.Model):
    link = models.URLField()

class ForeginPolicyArticle(models.Model):
    "Database model meant to represent an article from Foreign Policy magazine"
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=250)
    date_published = models.DateField()
    link = models.URLField()
    
    authors = models.ForeignKey(People, on_delete=models.SET_NULL, null=True)
    countries = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    page_refs = models.ForeignKey(ArticleLinks, on_delete=models.SET_NULL, null=True)

