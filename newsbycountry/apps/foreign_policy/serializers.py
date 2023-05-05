from rest_framework import serializers

from apps.foreign_policy import models

class ForeginPolicyArticleSerializer(serializers.HyperlinkedModelSerializer):

    page_refs = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="url"
    )

    countries = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )

    authors = serializers.StringRelatedField(many=True)
    rss_feed = serializers.StringRelatedField(many=False)

    class Meta:
        model = models.ForeginPolicyArticle
        fields = [
            "id", 
            "title", 
            "date_published", 
            "link", 
            "page_refs",
            "countries",
            "authors",
            "rss_feed",

            "has_entity_been_processed", 
            "has_entity_been_validated", 
            "processed_on",
            "validated_on"
            ]

class ForeginPolicyArticleRawTextSerializer(serializers.Serializer):
    "Returns the ID and the Raw text for the artricles"
    id = serializers.IntegerField(read_only=True)
    title=serializers.CharField(read_only=True)
    raw_text = serializers.SerializerMethodField(read_only=True)

    def get_raw_text(self, article_instance: models.ForeginPolicyArticle):
        "Apply the instance function to extract raw text from the html file of the Article object instance"        
        article_text = article_instance.get_text_from_html() if article_instance.file else None
        return article_text
    