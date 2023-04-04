from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static 

from newsbycountry import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.homepage, name="homepage"),
    path('foreign_policy/', include("apps.foreign_policy.urls"))
]

# Including a local static url for testing: 
