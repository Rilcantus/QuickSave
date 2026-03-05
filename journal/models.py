from django.db import models
from django.conf import settings
from games.models import Game
from play_sessions.models import Session


class JournalEntry(models.Model):
    """
    A reflection entry. Can be tied to a Session OR standalone for a Game.
    At least one of (session, game) must be set — enforced in clean().
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='journal_entries'
    )
    session = models.OneToOneField(
        Session,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entry'
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entries'
    )

    # Content
    body = models.TextField(blank=True)
    accomplishments = models.TextField(blank=True)
    blockers = models.TextField(blank=True)
    next_goals = models.TextField(blank=True)
    mood = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def get_game(self):
        """Return the game whether entry is session-based or standalone."""
        if self.session_id and self.session and self.session.game:
            return self.session.game
        if self.game_id and self.game:
            return self.game
        return None

    def __str__(self):
        game = self.get_game()
        return f"Journal — {game.title if game else 'Unknown'} — {self.created_at.strftime('%Y-%m-%d')}"