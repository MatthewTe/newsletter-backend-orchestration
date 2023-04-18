from django.db import models

# Create your models here.
class Links(models.Model):
    "Model meant to represent a url as a reference for other arguments"
    id = models.AutoField(primary_key=True)                                                                               
    url = models.URLField(unique=True, max_length=400)

    def __str__(self):
        return self.url

class Tags(models.Model):
    "A genertic tag content"
    name = models.CharField(max_length=250, unique=True)

    def __str__(self):
        return self.name

