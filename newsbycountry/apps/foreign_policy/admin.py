from django.contrib import admin

from apps.foreign_policy import models

# Register your models here.
admin.site.register(models.ForeginPolicyRssFeed)
admin.site.register(models.ForeginPolicyArticle)
admin.site.register(models.ArticleLinks)
