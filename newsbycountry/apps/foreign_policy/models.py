import io
import feedparser
import time
from celery import shared_task
from urllib.parse import urlparse, parse_qs
from nameparser import HumanName
from bs4 import BeautifulSoup
import validators 

from django.db import models
from django.core.files import File

# Base Model imports:
from newsbycountry.base_models import BaseRssEntry, BaseRSSFeed

from apps.people.models import People
from apps.geography.models import Country
from apps.references.models import Links, Tags

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



class ForeginPolicyRssFeed(BaseRSSFeed):
    "RSS Feed model for parsing Foreign Policy Articles"
    rss_feed_xml = models.FileField(upload_to="foreign_policy/rss_feed/%Y/%m/%d", null=True, blank=True)

    def extract_fields_from_xml_entry(self, rss_entry: dict) -> tuple:
        """Function takes in an rss entry dictionary and extracts the fields from this
        dict to create a ForeginPolicyArticle() object for the entry.
        """
        # First we de-structure all of the fields in the dictionary that are easy to destructure:
        title, article_link = rss_entry.title, rss_entry.link

        # This assumes the date values are in the format 
        # time.struct_time(tm_year=2023, tm_mon=3, tm_mday=12, tm_hour=14, tm_min=0, tm_sec=48, tm_wday=6, tm_yday=71, tm_isdst=0),
        date = datetime.datetime(*rss_entry.published_parsed[:6]) 
        date_w_timezone = pytz.timezone("GMT").localize(date)

        # Extracting the unique id from fp's id url as a query param. This is used as the primary key for the ForeginPolicyArticle model
        # and may need to be changed based on if it gets changed on fp's end (eg: it is no longer unique or gets provided from the rss feed in
        # a different way). Currently it assumes that the id paramter is provided in the form: https://foreignpolicy.com/?p=1106513
        id_url_params =  urlparse(rss_entry.id).query
        id = parse_qs(id_url_params)['p'][0]

        #article_response =requests.get(article_link)
        # Extracting the html bytes string for the article page:
        file = None

        # Extracting authors from the entry. 
        authors = self._parse_author_dict(rss_entry.authors)

        # Parsing the tags from the entry:
        tags = self._parse_tags_dict(rss_entry.tags)

        return id, title, date_w_timezone, article_link, file, authors, tags

    def _parse_author_dict(self, authors: List) -> List:
        """Parses the RSS feeds author dictionary to make it a data structure that is compatable with the Django Model used to represent
        People. Assumes the author dict is in the format:

        [{'name': 'Emma Ashford and Matthew Kroenig'}] and gets converted to the format:
        
        [
            {'first': 'Emma', 'last': 'Ashford'}
            {'first': 'Matthew', 'last': 'Kroenig'}
        ]
        """
        # Creating list to populate with correct author name structures:
        author_lst = []

        # Iterating through the provided list of dict:
        for author_dict in authors:
            # Splitting the single dict string into a list of individual names:
            names = author_dict['name'].split(' and ')
            

            # For each name in the split list, we create a NameParser object to abstract away the regex of determining first and
            # last names:
            for name_str in names:
                name = HumanName(name_str)

                author_lst.append(name.as_dict())
        
        return author_lst

    def _parse_tags_dict(self, tags: List) -> List:
        """Parses the FP tag dictionary to flatten the tags provided into a format that the extract_fields_from_xml_entry
        can make use of. 

        Assumes that the tags list comes in this format: 
        [{'term': 'Flash Points', 'scheme': None, 'label': None}, {'term': 'Eastern Europe', 'scheme': None, 'label': None}]
        
        And converts the tags into this:
        ['Flash Points', 'Eastern Europe']
        """
        return [tag['term'] for tag in tags]


    def save(self, *args, **kwargs):
        """
        """
        # Creating a variable to track all of the FP articles created from this rss feed to be connected back to it
        # via a post-save hook:
        self._fp_articles = []
        self.feed_source = "https://foreignpolicy.com/feed/"

        # Actually making the request to the FP rss feed endpoint for the xml:
        xml_bytes = self._get_xml_content_from_url(rss_endpoint=self.feed_source)

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
            ) = self.extract_fields_from_xml_entry(entry)

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
                tag_obj, tag_created = Tags.objects.get_or_create(
                    name=tag
                )

                # Connect the tag object via many-to-many:
                article_model.tags.add(tag_obj)

        super(ForeginPolicyRssFeed, self).save(*args, **kwargs) 

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

class ForeginPolicyArticle(BaseRssEntry):
    "Database model meant to represent an article from Foreign Policy magazine"

    def parse_html_for_page_links(self):
        """Parses the bytes for the uploaded html files to extract all of the links from the main content.
        For each link it checks to see if there already exists a Link model object with that url. It there
        is, that Link object is attached to the model via the page_refs ManyToMany Field. If that link does
        not exist then it is created and amd then attached
        """
        # passing in the article bytes to generate the list of links: 
        links_lst = self._get_links_from_article_html(self.file.read())

        for link in links_lst:
            link_obj, created = Links.objects.get_or_create(
                url=link
            )

            # Connecting the link object to the model (we just set the instance param, we do not save):
            self.page_refs.add(link_obj)

        print(f"Extracted {len(links_lst)} Links from article: {self.title}")

    def _query_raw_entry_html_content(self, article_url: str) -> bytes:
        """The function that makes a request for the html content for a fp article based on the
        url extracted from the rss feed. 

        This method is used inplace of just using the request object in the ForeginPolicyArticle model
        to add additional error catching or adding url proxy logic to making the request.
        """
        headers = {'Cookie': ''}
        article_response = requests.get(article_url, headers=headers)

        article_html_bytes = article_response.content

        # Add timing to prevent overloading endpoint:
        time.sleep(5)

        return article_html_bytes

    def _get_links_from_article_html(self, html_bytes: bytes) -> List:
        """
        """
        # Loading we just need the validated urls for the list so we load it into BS4 and pare the main content for hrefs:
        article_soup = BeautifulSoup(html_bytes, "html.parser")
        article_tag = article_soup.find("article", class_="article")
        article_content = article_tag.find_all("div", {"class":lambda x: x in ['content-gated', 'content-ungated']})

        # Building the main list of links from attribute tags from inside the articles content:
        links = []
        for div in article_content:
            for a_tag in div.find_all("a", href=True):
                links.append(a_tag["href"])

        # Scurbbing the list of links to only include unique and valid elements:
        unique_links = set(links)
        valid_links = [url for url in unique_links if validators.url(url)]

        return valid_links

    def save(self, *args, **kwargs):
        """Adds functionality that queried the Foregin Policy article html for the model entry and processes it.

        # TODO: Use post-save callback to process html from fp and extract links.
        https://stackoverflow.com/questions/43145712/calling-a-function-in-django-after-saving-a-model     
        """
        super(ForeginPolicyArticle, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.authors} on {self.date_published}"
    
