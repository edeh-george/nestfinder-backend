import uuid

from django.db import models


class UUIDModelAbstract(models.Model):
    """An abstract base class that creates a UUID attribute as the primary key of the model"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    class Meta:
        abstract = True
