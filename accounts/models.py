from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Steam integration
    steam_id = models.CharField(max_length=50, blank=True)
    steam_username = models.CharField(max_length=100, blank=True)
    steam_avatar = models.URLField(blank=True)
    steam_polling_enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.username