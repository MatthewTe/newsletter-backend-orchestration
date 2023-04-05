import io
import feedparser
import time
from celery import shared_task

from django.db import models
from django.core.files import File

from apps.people.models import People
from apps.geography.models import Country
from apps.references.models import Links

from apps.foreign_policy.processing_methods import load_rss_feed, utils

from django.db.models.signals import post_save
from django.dispatch import receiver

# Function that asyncronously processes each of the newly created FP Article model objects by adding them to the celery task que:
@shared_task()
def post_process_article_after_creation_task(rss_feed_instance_pk, newly_created_article_pk):

    # Querying the newly created RSS feed model object and the newly created model instance:
    newly_created_article = ForeginPolicyArticle.objects.get(pk=newly_created_article_pk)

    time.sleep(10)

    # Pulling down the html content based on the Article link param:
    newly_created_article.extract_article_html()

    # Parsing the html content for all relevant links and connecting them to the Article:
    newly_created_article.parse_html_for_page_links()

    # Connecting all of the article models to the RSS feed database object via their Foreign Key now that they have been created:
    
    # TODO: To fix the issue, perhaps have a signal be sent so that the task keeps retrying untill it succedes
    new_created_rss_feed = ForeginPolicyRssFeed.objects.get(pk=rss_feed_instance_pk)
    newly_created_article.rss_feed = new_created_rss_feed

    newly_created_article.save()



class ForeginPolicyRssFeed(models.Model):
    date_extracted = models.DateTimeField(auto_now_add=True)
    rss_feed_xml = models.FileField(upload_to="foreign_policy/rss_feed/%Y/%m/%d", null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        """
        # Creating a variable to track all of the FP articles created from this rss feed to be connected back to it
        # via a post-save hook:
        self._fp_articles = []

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
            if ForeginPolicyArticle.objects.filter(id=entry_id).exists():
                continue

            article_model = ForeginPolicyArticle(
                id=entry_id,
                title=entry_title,
                date_published=entry_date_w_timezone,
                link=entry_article_link,
                file=entry_file
            ) 
            article_model.save()

            self._fp_articles.append(article_model)

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

        super(ForeginPolicyRssFeed, self).save(*args, **kwargs) 

    def __str__(self):
        return f"Feed on {self.date_extracted}"

@receiver(post_save, sender=ForeginPolicyRssFeed) 
def post_processing_FP_article_objects(sender, instance, created, **kwargs):
    """
    A post save hook that performs all of the processing logic on the FP Article objects.
    It shoots off a celery task for processing the article contents. 

    It performs the following logic:
        - Attaches the FP Object to the current RSSFeed object
        - Make the http request to FP for the html content for each article
        - Parse the html to extract links from the html and create/connect each link object to the Article objcet.

    :param sender: The model class of the sender.
    :param instance: The instance of the model class that has been saved.
    :param created: A boolean indicating whether the instance was created or updated.
    :param kwargs: A dictionary of keyword arguments.
    """

    # Get the list of ForeignPolicyArticle objects associated with this RSS feed instance that was attached in the custom save method:
    fp_articles = getattr(instance, "_fp_articles", None)

    if fp_articles:
        for article in fp_articles:
            
            post_process_article_after_creation_task.delay(
                rss_feed_instance_pk=instance.pk,
                newly_created_article_pk=article.pk
            )


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
    file = models.FileField(null=True, blank=True, upload_to=utils.get_upload_path)
    
    authors = models.ManyToManyField(People)
    countries = models.ManyToManyField(Country)
    tags = models.ManyToManyField(ForeginPolicyTags)
    page_refs = models.ManyToManyField(Links)
    rss_feed = models.ForeignKey(ForeginPolicyRssFeed, on_delete=models.SET_NULL, null=True)

    def extract_article_html(self):
        """Method makes the http request to the provided link and extracts the html content
        of the article. It then sets the file object as the file variable to the object. 
        """
        fp_bytes = load_rss_feed.get_article_html_content(article_url=self.link)
        html_file = File(io.BytesIO(fp_bytes), name=f"article_{self.id}.html")
        self.file = html_file
        print(f"Queried Article html from: {self.title}, Size {len(fp_bytes)} bytes")        

    def parse_html_for_page_links(self):
        """Parses the bytes for the uploaded html files to extract all of the links from the main content.
        For each link it checks to see if there already exists a Link model object with that url. It there
        is, that Link object is attached to the model via the page_refs ManyToMany Field. If that link does
        not exist then it is created and amd then attached
        """
        # passing in the article bytes to generate the list of links: 
        links_lst = utils.get_links_from_article_html(self.file.read())

        for link in links_lst:
            link_obj, created = Links.objects.get_or_create(
                url=link
            )

            # Connecting the link object to the model (we just set the instance param, we do not save):
            self.page_refs.add(link_obj)

        print(f"Extracted {len(links_lst)} Links from article: {self.title}")

    def save(self, *args, **kwargs):
        """Adds functionality that queried the Foregin Policy article html for the model entry and processes it.

        # TODO: Use post-save callback to process html from fp and extract links.
        https://stackoverflow.com/questions/43145712/calling-a-function-in-django-after-saving-a-model     
        """
        super(ForeginPolicyArticle, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.authors} on {self.date_published}"
    
