from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
  """
  Custom user model for QuickSave.
  Extends Django's build in AbstractUser so we keep all the
  default auth functionality (login, password hashing, etc.)
  while giving ourselves room to add fields later. 
  """

  # Future fields can go here, eg:
  # avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
  # bio = models.TextField(blank=True)
  # timezone = models.CharField(max_length=50, default='UTC')

  def __str__(self):
    return self.username
  