from django.db.models.functions import Cast
from django.db.models import F
from django.db.models.expressions import Func
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, response

from apps.foreign_policy import models
from apps.foreign_policy import serializers

from bs4 import BeautifulSoup


class ForeginPolicyArticleViewSet(viewsets.ModelViewSet):
    queryset = models.ForeginPolicyArticle.objects.all()
    serializer_class = serializers.ForeginPolicyArticleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['title', "date_published"]
    
    def get_queryset(self):
        
        queryset = self.queryset

        # Processing queryset parameters and filtering the querytset:
        title = self.request.query_params.get('title', None)
        has_entity_been_processed = self.request.query_params.get('procssed', None)
        has_entity_been_validated = self.request.query_params.get('validated', None)

        if title is not None:
            queryset = queryset.filter(title=title)
        if has_entity_been_processed is not None:
            queryset = queryset.filter(has_entity_been_processed=has_entity_been_processed)
        if has_entity_been_validated is not None:
            queryset = queryset.filter(has_entity_been_validated=has_entity_been_validated)

        return queryset

class ForeginPolicyArticleRawTextViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.ForeginPolicyArticle.objects.all()
    serializer_class = serializers.ForeginPolicyArticleRawTextSerializer

    def get_queryset(self):

        queryset = self.queryset

        # Tries to filter by ID or returns full dataset:
        id_filter = self.kwargs["pk"] if "pk" in self.kwargs else None

        if id_filter:
            queryset = self.queryset.filter(id=id_filter)

        return queryset