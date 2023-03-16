import requests
import datetime
import pytz
import time
import io

from urllib.parse import urlparse, parse_qs

from django.core.files import File

from apps.foreign_policy.processing_methods import utils

def get_xml_from_current_daily_feed(rss_endpoint: str = "https://foreignpolicy.com/feed/") -> bytes:
    """Function takes the hardcoded rss feed url for FP articles and pulls down the 
    XML file. This xml file is then parsed and saved as a static file via the 
    ForeginPolicyRssFeed model.

    Returns the encoded XML file as a bytestring

    """
    response = requests.get(rss_endpoint)

    return response.content

def get_article_html_content(article_url: str) -> bytes:
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

def extract_fields_from_xml_entry(rss_entry: dict) -> tuple:
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
    authors = utils.parse_author_dict(rss_entry.authors)

    # Parsing the tags from the entry:
    tags = utils.parse_tags_dict(rss_entry.tags)

    return id, title, date_w_timezone, article_link, file, authors, tags