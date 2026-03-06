from django.utils import timezone
from accounts.steam import get_currently_playing
from games.models import Game
from games.rawg import search_games
from play_sessions.models import Session


def poll_steam_for_user(user_id):
    """
    Poll Steam for a user and auto-start/end sessions.
    Called by django-q every 5 minutes.
    """
    from accounts.models import User
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    if not user.steam_id or not user.steam_polling_enabled:
        return

    currently_playing = get_currently_playing(user.steam_id)
    active_session = Session.objects.filter(
        game__user=user,
        ended_at__isnull=True
    ).select_related('game').first()

    if currently_playing:
        game_name = currently_playing['name']

        # If already in a session for this game, do nothing
        if active_session and active_session.game.title.lower() == game_name.lower():
            return

        # End any other active session first
        if active_session:
            active_session.end()

        # Find or create the game
        game = Game.objects.filter(
            user=user,
            title__iexact=game_name
        ).first()

        if not game:
            # Auto-create the game
            game = Game(user=user, title=game_name)

            # Try to get cover art from RAWG
            results = search_games(game_name)
            if results and results[0]['image']:
                game.cover_image_url = results[0]['image']

            game.save()

        # Start a new session
        Session.objects.create(
            game=game,
            started_at=timezone.now(),
        )

    else:
        # Not playing anything — end active session if exists
        if active_session:
            active_session.end()


def schedule_steam_polling():
    """Schedule polling for all users with Steam connected."""
    from accounts.models import User
    from django_q.tasks import async_task

    users = User.objects.filter(
        steam_polling_enabled=True,
        steam_id__isnull=False
    ).exclude(steam_id='')

    for user in users:
        async_task('accounts.tasks.poll_steam_for_user', user.pk)

def poll_discord_for_user(user_id):
    """
    Poll Discord for a user and auto-start/end sessions.
    Called by django-q every 5 minutes.
    """
    from accounts.models import User
    from accounts.discord_api import get_currently_playing, refresh_access_token

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    if not user.discord_id or not user.discord_polling_enabled:
        return

    if not user.discord_access_token:
        return

    # Try to get currently playing
    currently_playing = get_currently_playing(user.discord_access_token)

    # If token expired try refreshing
    if currently_playing is None and user.discord_refresh_token:
        tokens = refresh_access_token(user.discord_refresh_token)
        if tokens and 'access_token' in tokens:
            user.discord_access_token = tokens['access_token']
            user.discord_refresh_token = tokens.get('refresh_token', user.discord_refresh_token)
            user.save()
            currently_playing = get_currently_playing(user.discord_access_token)

    active_session = Session.objects.filter(
        game__user=user,
        ended_at__isnull=True
    ).select_related('game').first()

    if currently_playing:
        game_name = currently_playing['name']

        # Already in a session for this game
        if active_session and active_session.game.title.lower() == game_name.lower():
            return

        # End any other active session
        if active_session:
            active_session.end()

        # Find or create game
        game = Game.objects.filter(
            user=user,
            title__iexact=game_name
        ).first()

        if not game:
            game = Game(user=user, title=game_name)
            results = search_games(game_name)
            if results and results[0]['image']:
                game.cover_image_url = results[0]['image']
            game.save()

        # Start session
        from django.utils import timezone
        Session.objects.create(
            game=game,
            started_at=timezone.now(),
        )

    else:
        if active_session:
            active_session.end()


def schedule_discord_polling():
    """Schedule polling for all users with Discord connected."""
    from accounts.models import User
    from django_q.tasks import async_task

    users = User.objects.filter(
        discord_polling_enabled=True,
        discord_id__isnull=False
    ).exclude(discord_id='')

    for user in users:
        async_task('accounts.tasks.poll_discord_for_user', user.pk)