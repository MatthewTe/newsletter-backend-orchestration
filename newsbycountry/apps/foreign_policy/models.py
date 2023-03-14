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

            # Create a model for the Article and save it now so that we can connect the Tag and Author objects:
            article_model = ForeginPolicyArticle(
                id=entry_id,
                title=entry_title,
                date_published=entry_date_w_timezone,
                link=entry_article_link,
                file=entry_file
            ) 
            article_model.save()

            # Authors and Tags are relational fields and as such depend on the existence of these models in the database. Here
            # we check to see if the People and Tag entries exist and if they do not then we need to create them:
            for author in entry_authors:
                # First we create the object.
                author_obj, author_created = People.objects.get_or_create(
                    first_name=author["first"],
                    last_name=author["last"]
                )

                # Then we connect it to the previously created article model instance:
                article_model.authors.add(author_obj)
            
            for tag in entry_tags:

                # Create the tag object:
                tag_obj, tag_created = ForeginPolicyTags.objects.get_or_create(
                    name=tag
                )

                # Connect the tag object via many-to-many:
                article_model.tags.add(tag_obj)

            # TODO: Try to assign the foregin key connection between this and the Article now inside the save. if not do it in a post save callback.

        super(ForeginPolicyRssFeed, self).save(*args, **kwargs) 

    def __str__(self):
        return f"Feed on {self.date_extracted}"
    
class ArticleLinks(models.Model):                                                                               
    link = models.URLField()

class ForeginPolicyTags(models.Model):
    """Represents article tags."""
    name = models.CharField(max_length=250, unique=True)

    def __str__(self):
        return self.name

class ForeginPolicyArticle(models.Model):
    "Database model meant to represent an article from Foreign Policy magazine"
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=250)
    date_published = models.DateField()
    link = models.URLField()
    file = models.FileField(null=True, blank=True)  # TODO: Add file path dir to store data in.
    
    authors = models.ManyToManyField(People)
    countries = models.ManyToManyField(Country)
    tags = models.ManyToManyField(ForeginPolicyTags)
    page_refs = models.ManyToManyField(ArticleLinks)
    rss_feed = models.ForeignKey(ForeginPolicyRssFeed, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        """Adds functionality that queried the Foregin Policy article html for the model entry and processes it.

        # TODO: Use post-save callback to process html from fp and extract links.
        https://stackoverflow.com/questions/43145712/calling-a-function-in-django-after-saving-a-model     
        """
        self.file = None

        super(ForeginPolicyArticle, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.authors} on {self.date_published}"