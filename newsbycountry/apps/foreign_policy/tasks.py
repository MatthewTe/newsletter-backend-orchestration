from celery import shared_task
import requests
import datetime

from apps.geography import models as geo_models
from apps.foreign_policy import models as fp_models

# TODO: Refactor tasks to be classes:
# https://docs.celeryq.dev/en/latest/userguide/tasks.html
# https://stackoverflow.com/questions/41933814/how-to-pass-a-class-based-task-into-celery-beat-schedule


@shared_task()
def parse_html_content_for_links_for_specific_models(fp_model_pk):
    """Celery task that calls an internal method in an Article to process the raw html for links on the page. This function only exists 
    to serve as a wrapper on an existing internal model method so that it can be called asyncronously
    """
    fp_model = fp_models.ForeginPolicyArticle.objects.get(pk=fp_model_pk)
    fp_model.parse_html_for_page_links()
    fp_model.page_refs_processed = True
    fp_model.page_refs_processed_on = datetime.datetime.now()
    fp_model.save()

@shared_task()
def parse_html_content_for_country_mentions(fp_model_pk):
    """Celery task that parses the Article's raw text content and extracts every mention of a country.
    It does this by accessing the  NLP REST API to generate NER tokens, remmaps these tokens into the correct
    country names based on existing remaps valens and then creates a connection between the article and the
    Country database model.
    """
    fp_model = fp_models.ForeginPolicyArticle.objects.get(pk=fp_model_pk)
    if fp_model.country_validated:
        return 
    
    article_raw_text = fp_model.get_text_from_html()

    ner_api_response = requests.post("http://configs-nlp_api-1:8000/article/", json={
            "id": fp_model.id,
            "title": fp_model.title,
            "raw_text": article_raw_text
        })
    ner_api_response.raise_for_status()

    gpe_labels = [label for label in ner_api_response.json() if label['label_type'] == "GPE"]
    
    # First we naively try to create connections to the Country objects:
    unique_detected_countries_in_text = [country for country in  geo_models.Country.objects.filter(
        name__in=[label["label"] for label in gpe_labels]) if country not in fp_model.countries.all()]

    for country_model in unique_detected_countries_in_text:
        print(f"{country_model.name} ADDED FROM DETECTED")
        fp_model.countries.add(country_model)

    # Then we use the country remaps model to determine if there are any other labels that are countries we can add:
    # We create new remaps or get existing ones from the db. If we find remaps that have FK connections to Country objects we map article to country:
    remap_country_objs = [
        geo_models.CountryEntityRemaps.objects.get_or_create(remap_name= label["label"]) for label in gpe_labels 
        if label['label'] not in [country.name for country in unique_detected_countries_in_text] or label['label'] not in [country.name for country in fp_model.countries.all()]
    ]

    for remap_obj, obj_created in remap_country_objs:
         if not obj_created and remap_obj.iso_country_name and remap_obj.iso_country_name not in [country for country in fp_model.countries.all()]:
              # This is the only condition where we would use a remap to add a Country connection to the Article. The remaps object already existed
              # and the remap object was connected to a Country (it already had a remap) so we connect the article to that remaps' country obj:
              print(f"{remap_obj.iso_country_name} ADDED FROM REMAP")
              fp_model.countries.add(remap_obj.iso_country_name)
    
    fp_model.country_processed = True
    fp_model.country_processed_on = datetime.datetime.now()
    fp_model.save()