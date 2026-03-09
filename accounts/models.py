from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Steam integration
    steam_id = models.CharField(max_length=50, blank=True)
    steam_username = models.CharField(max_length=100, blank=True)
    steam_avatar = models.URLField(blank=True)
    steam_polling_enabled = models.BooleanField(default=False)

    # Discord integration
    discord_id = models.CharField(max_length=50, blank=True)
    discord_username = models.CharField(max_length=100, blank=True)
    discord_avatar = models.URLField(blank=True)
    discord_access_token = models.TextField(blank=True)
    discord_refresh_token = models.TextField(blank=True)
    discord_polling_enabled = models.BooleanField(default=False)

    # Xbox integration
    xbox_id = models.CharField(max_length=50, blank=True)
    xbox_gamertag = models.CharField(max_length=100, blank=True)
    xbox_avatar = models.URLField(blank=True)
    xbox_access_token = models.TextField(blank=True)
    xbox_refresh_token = models.TextField(blank=True)
    xbox_token_expires = models.DateTimeField(null=True, blank=True)
    xbox_polling_enabled = models.BooleanField(default=False)

    # PSN integration
    psn_username = models.CharField(max_length=100, blank=True)
    psn_account_id = models.CharField(max_length=50, blank=True)
    psn_avatar = models.URLField(blank=True)
    psn_polling_enabled = models.BooleanField(default=False)

    # Roblox integration
    roblox_username = models.CharField(max_length=100, blank=True)
    roblox_user_id = models.CharField(max_length=50, blank=True)
    roblox_avatar = models.URLField(blank=True)
    roblox_polling_enabled = models.BooleanField(default=False)

    # Subscription
    is_pro = models.BooleanField(default=False)

    @property
    def psn_avatar_url(self):
        """Return PSN avatar URL forced to HTTPS."""
        if self.psn_avatar:
            return self.psn_avatar.replace('http://', 'https://', 1)
        return ''

    def __str__(self):
        return self.username