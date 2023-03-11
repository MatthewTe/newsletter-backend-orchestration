from rest_framework import routers
from django.urls import path, include

from apps.foreign_policy import viewsets

foreign_policy_router = routers.DefaultRouter()

foreign_policy_router.register(r"articles", viewsets.ForeginPolicyArticleViewSet)

urlpatterns = [
    path("api", include(foreign_policy_router.urls))
]