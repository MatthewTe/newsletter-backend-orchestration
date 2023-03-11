from rest_framework import serializers

from apps.foreign_policy import models

class ForeginPolicyArticleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.ForeginPolicyArticle
        fields = "__all__"
        read_only_fields = ["authors", "countries", "page_refs"]