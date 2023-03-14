from django.db import models
import uuid

class People(models.Model):
    """The core database model meant to represent a person of interest for the whole application"""
    id =  models.UUIDField(primary_key=True, default=uuid.uuid4)
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"