from ast import List

from nameparser import HumanName
from bs4 import BeautifulSoup
import validators 

def get_upload_path(instance, filename):
    "Formats the upload to filepath for placing articles in a directory that correlates with the day that the article was created not uploaded"
    return "foreign_policy/articles/{}/{}/{}/{}".format(
        instance.date_published.year,
        instance.date_published.month,
        instance.date_published.day,
        filename
    )

def parse_author_dict(authors: List) -> List:
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

def parse_tags_dict(tags: List) -> List:
    """Parses the FP tag dictionary to flatten the tags provided into a format that the extract_fields_from_xml_entry
    can make use of. 

    Assumes that the tags list comes in this format: 
    [{'term': 'Flash Points', 'scheme': None, 'label': None}, {'term': 'Eastern Europe', 'scheme': None, 'label': None}]
    
    And converts the tags into this:
    ['Flash Points', 'Eastern Europe']
    """
    return [tag['term'] for tag in tags]

def get_links_from_article_html(html_bytes: bytes) -> List:
    
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