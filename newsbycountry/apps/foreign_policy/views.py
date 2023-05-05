from django.shortcuts import render

from apps.foreign_policy import models

import datetime

def render_daily_articles(request):
    
    context = {}

    date = datetime.datetime.today()
    daily_articles = models.ForeginPolicyArticle.objects.filter(date_published=date)
    context["articles"] = daily_articles
    context["today"] = date

    # TODO: Continue development of this logic - debug connection issue
    text_data = models.ForeginPolicyArticle.objects.first().perform_ner_on_text(
        country_ndr_endpoint="http://0.0.0.0:8001/article/"
    )
    print(text_data)

    return render(request, "foreign_policy/display_daily_articles.html", context=context)

def display_article(request, id:int):

    context={}

    article = models.ForeginPolicyArticle.objects.get(id=id)
    context["article"] = article

    return render(request, "foreign_policy/display_article.html", context=context)