from rest_framework import routers
from django.urls import path, include

from apps.data_labeler import views

urlpatterns = [
    path("daily_dashboard", views.daily_pipeline_ingestion_dashboard, name="daily_article_dashboard"),
    path("ner_dashboard", views.ner_labeler_dashboard, name="ner_dashboard"),
    path("foreign_policy/dashboard/<int:id>", views.fp_article_nlp_dashboard, name="fp_article_dashboard")
]