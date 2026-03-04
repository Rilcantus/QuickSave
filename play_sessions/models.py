from django.db import models
from django.conf import settings
from django.utils import timezone
from games.models import Game, Descriptor, CustomFieldDefinition


class Session(models.Model):
    """
    A single play period for a game.
    Tracks time and links to an optional descriptor and custom field values.
    """

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    descriptor = models.ForeignKey(
        Descriptor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions'
    )
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['game', '-started_at']),
        ]

    def end(self):
        """End the session and compute duration."""
        self.ended_at = timezone.now()
        self.duration_seconds = int(
            (self.ended_at - self.started_at).total_seconds()
        )
        self.save()

    @property
    def is_active(self):
        """True if the session has been started but not yet ended."""
        return self.ended_at is None

    @property
    def duration_display(self):
        """Human-readable duration e.g. '1h 23m'"""
        if not self.duration_seconds:
            return None
        hours, remainder = divmod(self.duration_seconds, 3600)
        minutes = remainder // 60
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def __str__(self):
        return f"{self.game.title} — {self.started_at.strftime('%Y-%m-%d %H:%M')}"


class CustomFieldValue(models.Model):
    """
    Stores the per-session value for a CustomFieldDefinition.
    Both 'text' and 'choice' types store their value as a string.
    """

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='custom_field_values'
    )
    field_definition = models.ForeignKey(
        CustomFieldDefinition,
        on_delete=models.CASCADE,
        related_name='values'
    )
    value = models.CharField(max_length=500, blank=True)

    class Meta:
        unique_together = [('session', 'field_definition')]

    def __str__(self):
        return f"{self.field_definition.name}: {self.value}"