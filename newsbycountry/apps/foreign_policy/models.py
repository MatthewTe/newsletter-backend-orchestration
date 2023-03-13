import io
import feedparser

from django.db import models
from django.core.files import File

from apps.people.models import People
from apps.geography.models import Country

from apps.foreign_policy.processing_methods import load_rss_feed 

class ForeginPolicyRssFeed(models.Model):
    date_extracted = models.DateTimeField(auto_now_add=True)
    rss_feed_xml = models.FileField(upload_to="foreign_policy/rss_feed/%Y/%m/%d", null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        """
        # Actually making the request to the FP rss feed endpoint for the xml:
        xml_bytes = load_rss_feed.get_xml_from_current_daily_feed()

        # Creating django File object from xml bytes string:
        xml_file = File(io.BytesIO(xml_bytes), name="foreign_policy_rss_feed.xml")
        self.rss_feed_xml = xml_file

        # Now that the rss feed has been extracted we can load it in python and parse it:
        rss_parser =  feedparser.parse(xml_bytes)

        # We can iterate over each article in the RSS feed and create ForeginPolicyArticle model instances
        # for each article:
        for entry in rss_parser.entries:

            # All variables easily extracted from the xml are done so here. The bulk of the processing logic is done in the
            # ForeginPolicyArticle model:
            (
                entry_id, entry_title, entry_date_w_timezone, 
                entry_article_link, entry_file, entry_authors, 
                entry_tags
            ) = load_rss_feed.extract_fields_from_xml_entry(entry)

            # Authors and Entries are relational fields and as such depend on the existence of these models in the database. Here
            # we check to see if the People and Tag entries exist and if they do not then we need to create them:
            

            new_article= ForeginPolicyArticle(
                id=entry_id,
                title=entry_title,
                date_published=entry_date_w_timezone,
                link=entry_article_link,
                authors=entry_authors,
                tags=entry_tags
            )

            new_article.save()


        super(ForeginPolicyRssFeed, self).save(*args, **kwargs) 


class ArticleLinks(models.Model):                                                                               
    link = models.URLField()

class ForeginPolicyTags(models.Model):
    """Represents article tags."""
    name = models.CharField(max_length=250)

class ForeginPolicyArticle(models.Model):
    "Database model meant to represent an article from Foreign Policy magazine"
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=250)
    date_published = models.DateField()
    link = models.URLField()
    file = models.FileField(null=True, blank=True) 
    
    authors = models.ForeignKey(People, on_delete=models.SET_NULL, null=True)
    countries = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    tags = models.ForeignKey(ForeginPolicyTags, on_delete=models.SET_NULL, null=True)
    page_refs = models.ForeignKey(ArticleLinks, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        """Adds functionality that queried the Foregin Policy article html for the model entry and processes it.

        This includes:
           - Making the request to FP for the article and saving the HTML to filstorage
           - Parsing the html to extract all of the urls from the page and creating link database entries (ArticleLinks) which 
             that are connected to the Article via foreign keys.
           - Parsing the author information from the author string variable to connect them to the People database object.
           - Extracting the tag and connecting them to Tag entries.
     
        """
        print("ASHFIUAHEUIFTASHEDUIFHIAUSEDHFUIASEHFUI")
        print(self.authors, self.tags)

        super(ForeginPolicyArticle, self).save(*args, **kwargs)
