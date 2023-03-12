from rest_framework import viewsets

from apps.foreign_policy import models
from apps.foreign_policy import serializers

class ForeginPolicyArticleViewSet(viewsets.ModelViewSet):
    queryset = models.ForeginPolicyArticle.objects.all()
    serializer_class = serializers.ForeginPolicyArticleSerializer