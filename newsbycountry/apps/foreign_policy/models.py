from django.db import models

from apps.people.models import People
from apps.geography.models import Country

class ForeginPolicyRssFeed(models.Model):
    date_extracted = models.DateTimeField(auto_now_add=True)
    rss_feed_xml = models.FileField()    

class ArticleLinks(models.Model):
    link = models.URLField()

class ForeginPolicyArticle(models.Model):
    "Database model meant to represent an article from Foreign Policy magazine"
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=250)
    date_published = models.DateField()
    link = models.URLField()
    file = models.FileField(null=True, blank=True) 
    
    authors = models.ForeignKey(People, on_delete=models.SET_NULL, null=True)
    countries = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    page_refs = models.ForeignKey(ArticleLinks, on_delete=models.SET_NULL, null=True)

    def save(*args, **kwargs):
        """Adds functionality that queried the Foregin Policy article html for the model entry and processes it.

        This includes:
           - Making the request to FP for the article and saving the HTML to filstorage
           - Parsing the html to extract all of the urls from the page and creating link database entries (ArticleLinks) which 
             that are connected to the Article via foreign keys.
           - Parsing the author information from the author string variable to connect them to the People database object.
           - Extracting the tag and connecting them to Tag entries.
     
        """


        super(ForeginPolicyArticle, self).save(*args, **kwargs)
