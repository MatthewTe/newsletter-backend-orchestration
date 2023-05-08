from ast import List
import requests
import time
import base64
import datetime

from django.core.files import File
from django.core.files.base import ContentFile

from django.db import models
from django.core.files import File

from apps.people.models import People
from apps.geography.models import Country
from apps.references.models import Links, Tags

from django.db.models.signals import post_save
from django.dispatch import receiver

# Base abstract classes for building the RSS feed ingestion pipelines:
class BaseRSSFeed(models.Model):
    """
    A base abstract class for building RSS feed ingestion pipelines. 

    Params:
        date_extracted (models.DateTileField): The automatic date time field indicated when the model entry was created.
        
        rss_feed_xml (models.FileField): model field representing the actual xlm file of the RSS feed extracted. Typically
            needs to be overwrited in order to modify the upload_to path for specific rss feeds.

        feed_source (models.URLField): Field representing the name of the rss feed. Is used as a metadata field for other
            processes associated with it such as naming file paths in their associated RSSEntry models and is required.

    """
    date_extracted = models.DateTimeField(auto_now_add=True)
    rss_feed_xml = models.FileField(upload_to="base/rss_feed/%Y/%m/%d", null=True, blank=True)
    feed_source = models.URLField()

    def __str__(self):
        return f"{self.feed_source} Feed on {self.date_extracted}"

    def _get_xml_content_from_url(self, rss_endpoint: str) -> bytes:
        """
        Returns the XML content from the given RSS feed URL.

        Args:
            rss_endpoint (str): The URL of the RSS feed.

        Returns:
            bytes: The XML content of the RSS feed.
        """
        response = requests.get(rss_endpoint)
        return response.content

    def extract_fields_from_xml_entry(rss_entry: dict) -> tuple:
        """
        Extracts relevant fields from a given RSS feed entry. Meant to be overwritten for each custom feed implementation

        Args:
            rss_entry (dict): A dictionary representing an RSS feed entry.

        Returns:
            tuple: A tuple containing relevant fields from the RSS feed entry.
        """
        pass
    
    def save(self, *args, **kwargs):
        """   
        """
        super(BaseRSSFeed, self).save(*args, **kwargs)

    class Meta:
        abstract = True

class BaseRssEntry(models.Model):
    """
    A model representing an RSS feed entry.

    Params:
        id (models.IntegerField): The primary key for each entry. Typically this field is populated by external logic 
            in the save method of the RSSFeed Model.
        
    Main Fields:

        These are more traditional fields containing information about the RSS Entry that get set during the inital parsing
        of the RSS Feed XML. Typically these fields are extraced durin the RSSFeed models' save function and then set during
        the same save function or post save hook of the RSSFeed model.

        title (models.Charfield)
        date_published (models.DateField)
        link (models.URLField)
        file (models.FileField)

    Relational Fields:

        These field are populated by internal methods of the Model, traditionally executed asyncronoulsy via some kind of
        process schedler or message que:

        authors (models.ManyToManyField)
        countries (models.ManyToManyField) 


    """

    # The unique ID of each model:
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=250)
    date_published = models.DateField()    
    link = models.URLField()

    file = models.FileField(null=True, blank=True)    
    file_processed = models.BooleanField(default=False)
    file_processed_on  = models.DateTimeField(blank=True, null=True)
    file_validated = models.BooleanField(default=False)
    file_validated_on = models.DateTimeField(blank=True, null=True)

    authors = models.ManyToManyField(People)
    authors_processed = models.BooleanField(default=False)
    authors_processed_on =  models.DateTimeField(blank=True, null=True)
    authors_validated = models.BooleanField(default=False)
    authors_validated_on = models.DateTimeField(blank=True, null=True)

    countries = models.ManyToManyField(Country)
    country_processed = models.BooleanField(default=False)
    country_processed_on = models.DateTimeField(blank=True, null=True)
    country_validated = models.BooleanField(default=False)
    country_validated_on = models.DateTimeField(blank=True, null=True)

    tags = models.ManyToManyField(Tags)
    tags_processed = models.BooleanField(default=False)
    tags_processed_on  = models.DateTimeField(blank=True, null=True)
    tags_validated = models.BooleanField(default=False)
    tags_validated_on = models.DateTimeField(blank=True, null=True)

    page_refs = models.ManyToManyField(Links)
    page_refs_processed = models.BooleanField(default=False)
    page_refs_processed_on = models.DateTimeField(blank=True, null=True)
    page_refs_validated = models.BooleanField(default=False)
    page_refs_validated_on = models.DateTimeField(blank=True, null=True)

    rss_feed = models.ForeignKey(BaseRSSFeed, on_delete=models.SET_NULL, null=True)

    # Meta Data Fields: for models:
    has_entity_been_processed = models.BooleanField(default=False)
    has_entity_been_validated = models.BooleanField(default=False)
    processed_on = models.DateTimeField(blank=True, null=True)
    validated_on = models.DateTimeField(blank=True, null=True)

    def extract_article_html(self):
        """
        Extracts the HTML content of the article from the RSS feed entry's URL link and stores it in a file field.
        """
        if not self.file_validated:
            return 

        raw_bytes = self._query_raw_entry_html_content(article_url=self.link)
        print("raw bytes!!!!!!!!!!!!!")
        html_file = ContentFile(raw_bytes)
        self.file.save(f"entry_{self.id}.html", html_file)
        print(f"Queried Article html from: {self.title}, Size {len(raw_bytes)} bytes")
        
        # Currently Processing and Validating the file field automatically:
        self.file_processed = True
        self.file_processed_on = datetime.datetime.now()
        self.file_validated = True
        self.file_validated_on = datetime.datetime.now()

    def parse_html_for_page_links(self):
        """
        Parses the HTML content of the article to extract all links from the main content, and attaches each link to
        the RSS feed entry using the page_refs ManyToMany Field. If a link already exists as a Link model object, it
        is reused; otherwise, it is created and then attached.
        """
        # passing in the article bytes to generate the list of links: 
        links_lst = self._get_links_from_article_html(self.file.read())

        for link in links_lst:
            link_obj, created = Links.objects.get_or_create(
                url=link
            )

            # Connecting the link object to the model (we just set the instance param, we do not save):
            self.page_refs.add(link_obj)

    def get_text_from_html(html_bytes: bytes) -> str:
        """
        """
        pass

    def parse_html_for_tags(self):
        """
        """
        pass

    def perform_ner_on_text(self, country_ndr_endpoint: str):
        """Extracting the raw text content from the article's html file and connecting the 
        Article to Country object:
        """
        # Extracting the raw text from html file and cerating JSON object of data:
        article_json = {
            "id": self.pk,
            "title":self.title,
            "raw_text":self.get_text_from_html()
        }

        # Request to NLP Country API enpoint. Expects response as a JSON of spaCy entites:
        ner_response = requests.post(country_ndr_endpoint, data=article_json)

        return ner_response


    def save(self, *args, **kwargs):
        """   
        """
        super(BaseRssEntry, self).save(*args, **kwargs)


    def _get_links_from_article_html(self, html_bytes: bytes) -> List:
        """
        Extracts all links from the given HTML bytes.

        Args:
            html_bytes (bytes): The HTML content of the article.

        Returns:
            List: A list of URLs extracted from the HTML.
        """
        pass
    
    def _query_raw_entry_html_content(self, article_url: str) -> bytes:
        """
        Queries the raw HTML content of the article from the given URL link.

        Args:
            article_url (str): The URL link to the article.

        Returns:
            bytes: The raw HTML content of the article.
        """
        headers = {'Cookie': ''}
        article_response = requests.get(article_url, headers=headers)

        article_html_bytes = article_response.content

        # Add timing to prevent overloading endpoint:
        time.sleep(5)

        return article_html_bytes

    def _parse_html_file_for_raw_text(self, html_bytes: bytes) -> str:
        """
        """
        pass

    class Meta:
        abstract = True

