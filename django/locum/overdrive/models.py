from django.db import models
from django.utils import timezone


class Token(models.Model):

    barcode = models.CharField(max_length=16, null=True, unique=True)
    access_token = models.CharField(max_length=1024, null=True)
    token_type = models.CharField(max_length=32, null=True)
    token_expiration = models.DateTimeField(null=True)

    def is_expired(self):
        return bool(
            self.token_expiration
            and self.token_expiration < timezone.now())
