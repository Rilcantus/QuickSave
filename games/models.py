from django.db import models
from django.conf import settings

# Create your models here.
class Game(models.Model):
  """A game the user plays. Root of everything in QuickSave"""

  STATUS_PLAYING = 'playing'
  STATUS_COMPLETED = 'completed'
  STATUS_DROPPED = 'dropped'
  STATUS_BACKLOG = 'backlog'

  STATUS_CHOICES = [
      (STATUS_PLAYING, 'Playing'),
      (STATUS_COMPLETED, 'Completed'),
      (STATUS_DROPPED, 'Dropped'),
      (STATUS_BACKLOG, 'Backlog'),
  ]

  user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='games'
  )
  title = models.CharField(max_length=200)
  platform = models.CharField(max_length=100, blank=True)
  cover_image_url = models.URLField(blank=True)
  status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLAYING, blank=True)
  rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-10
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['-updated_at']
    indexes = [
      models.Index(fields=['user', 'title']),
    ]
  
  def __str__(self):
    return f"{self.title} ({self.user.username})"
  

class Descriptor(models.Model):
  """
  Optional run label for a session.
  e.g 'STR Build', 'Modded Run', 'Ranked Season 5'
  Scoped per game so names dont bleed across games.
  """

  game = models.ForeignKey(
    Game,
    on_delete=models.CASCADE,
    related_name='descriptors'
  )
  name = models.CharField(max_length=100)
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    ordering = ['name']
    unique_together = [('game', 'name')]

  def __str__(self):
    return f"{self.name} — {self.game.title}"


class CustomFieldDefinition(models.Model):
    """
    Defines what metadata a user wants to track per game.
    e.g. 'Character Name', 'Difficulty', 'Build'
    """

    class FieldType(models.TextChoices):
        TEXT = 'text', 'Text'
        CHOICE = 'choice', 'Choice (dropdown)'

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='custom_field_definitions'
    )
    name = models.CharField(max_length=100)
    field_type = models.CharField(
        max_length=20,
        choices=FieldType.choices,
        default=FieldType.TEXT
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        unique_together = [('game', 'name')]

    def __str__(self):
        return f"{self.name} ({self.get_field_type_display()}) — {self.game.title}"


class CustomFieldChoice(models.Model):
    """
    Reusable dropdown options for a 'choice' type CustomFieldDefinition.
    Options are accumulated automatically as users enter new values.
    """

    field_definition = models.ForeignKey(
        CustomFieldDefinition,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    value = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['value']
        unique_together = [('field_definition', 'value')]

    def __str__(self):
        return f"{self.value} — {self.field_definition.name}"