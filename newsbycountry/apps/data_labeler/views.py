from django.shortcuts import render

from apps.foreign_policy import models as fp_models
from apps.geography import models as geo_models

import requests

# https://towardsdatascience.com/named-entity-recognition-with-nltk-and-spacy-8c4a7d88e7da
def daily_pipeline_ingestion_dashboard(request):
    """Django view that queries and renders all components that were ingested that are tagged for todays date."""
    context = {} 
    
    # Getting Foreign Policy Articles:


    return render(request, "data_labeler/dailypipeline_ingestion_dashboard.html", context=context)

def ner_labeler_dashboard(request):
    """View that renders the dashboard for manually associating relationships between NER Labels
    and internal models. 

    Generates a list of Article objects that have not been verified/processed and outputs them to
    the template for NLP processing.
    """
    context = {}

    # Add more models here as we add more to the dashboard:
    unprocessed_fp_articles = fp_models.ForeginPolicyArticle.objects.filter(
        has_entity_been_processed=False,
        has_entity_been_validated=False
    ).values("id", "title", "date_published", "country_processed")
    
    context["articles"] = unprocessed_fp_articles

    return render(request, "data_labeler/ner_labeler_dashboard.html", context=context)

def fp_article_nlp_dashboard(request, id: int):
    """Renders specific content for an FP article that allows the user to perform the manual
    data labeling for NLP tasks.
    """
    fp_article = fp_models.ForeginPolicyArticle.objects.get(id=id)
    raw_text = fp_article.get_text_from_html()

    context = {
        "article":fp_article,
        "raw_text":raw_text
    }

    # If there has been a POST request then make a request to the NLP API to extract NER for the text content:
    if request.method == "POST":
        ner_api_response = requests.post("http://configs-nlp_api-1:8000/article/", json={
            "id": fp_article.id,
            "title": fp_article.title,
            "raw_text": raw_text
        })
        ner_api_response.raise_for_status()

        gpe_labels = [label for label in ner_api_response.json() if label['label_type'] == "GPE"]

        # First to process this we need to check and see if any of the labels match correctly to country names:
        detected_countries_in_text = [country.name for country in  geo_models.Country.objects.filter(name__in=[label["label"] for label in gpe_labels])]

        # Skip over labels that are deteced as countries, only create remaps for non-auto matched labels:
        # Only loading GPE labels: (obj, created)
        processed_ner = [
            geo_models.CountryEntityRemaps.objects.get_or_create(remap_name=label['label'])
            for label in gpe_labels if label["label"] not in detected_countries_in_text
        ]

        context["total_article_entities"] = gpe_labels
        context["newly_created_article_entities"] = [entity_remap[0].remap_name for entity_remap in processed_ner if entity_remap[1] == True]

    return render(request, "data_labeler/fp_article_ner_view.html", context=context)

