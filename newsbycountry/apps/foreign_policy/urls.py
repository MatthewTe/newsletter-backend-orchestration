from rest_framework import routers
from django.urls import path, include

from apps.foreign_policy import viewsets
from apps.foreign_policy import views

foreign_policy_router = routers.DefaultRouter()

foreign_policy_router.register(r"articles", viewsets.ForeginPolicyArticleViewSet)
foreign_policy_router.register(r"article_text", viewsets.ForeginPolicyArticleRawTextViewSet)

urlpatterns = [
    path("daily", views.render_daily_articles, name="view_daily_articles"),
    path("article/<int:id>", views.display_article, name="display_single_article"),
    path("api/", include(foreign_policy_router.urls))
]