from django.shortcuts import render


# https://towardsdatascience.com/named-entity-recognition-with-nltk-and-spacy-8c4a7d88e7da
def daily_pipeline_ingestion_dashboard(request):
    """Django view that queries and renders all components that were ingested that are tagged for todays date."""
    context = {} 
    
    # Getting Foreign Policy Articles:

    return render(request, "data_labeler/dailypipeline_ingestion_dashboard.html", context=context)