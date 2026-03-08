from django.utils import timezone
from games.models import Game
from games.rawg import search_games
from play_sessions.models import Session


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _get_or_create_game(user, game_name):
    """Find or create a game for a user, fetching cover art if new."""
    game = Game.objects.filter(user=user, title__iexact=game_name).first()
    if not game:
        game = Game(user=user, title=game_name)
        results = search_games(game_name)
        if results and results[0]['image']:
            game.cover_image_url = results[0]['image']
        game.save()
    return game


def _handle_presence(user, game_name, source):
    """
    Core logic for handling a platform presence update.
    - If already in a session for this game, do nothing.
    - If another platform owns the active session, do nothing.
    - If this platform owns the active session, end it and start a new one.
    - If no active session, start one.
    """
    active_session = Session.objects.filter(
        game__user=user,
        ended_at__isnull=True
    ).select_related('game').first()

    if game_name:
        # Already tracking this exact game
        if active_session and active_session.game.title.lower() == game_name.lower():
            return

        # Another platform owns the session — don't touch it
        if active_session and active_session.source != source:
            return

        # End our own session before starting a new one
        if active_session:
            active_session.end()

        game = _get_or_create_game(user, game_name)
        Session.objects.create(
            game=game,
            started_at=timezone.now(),
            source=source,
        )

    else:
        # Not playing — only end session if we own it
        if active_session and active_session.source == source:
            active_session.end()


def _schedule_all(model_filter, task_path):
    """Generic scheduler — finds eligible users and queues async tasks."""
    from django_q.tasks import async_task
    for user in model_filter:
        async_task(task_path, user.pk)


# ─── STEAM ────────────────────────────────────────────────────────────────────

def poll_steam_for_user(user_id):
    from accounts.models import User
    from accounts.steam import get_currently_playing
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    if not user.steam_id or not user.steam_polling_enabled:
        return
    result = get_currently_playing(user.steam_id)
    _handle_presence(user, result['name'] if result else None, Session.SOURCE_STEAM)


def schedule_steam_polling():
    from accounts.models import User
    _schedule_all(
        User.objects.filter(steam_polling_enabled=True).exclude(steam_id=''),
        'accounts.tasks.poll_steam_for_user'
    )


# ─── DISCORD ──────────────────────────────────────────────────────────────────

def poll_discord_for_user(user_id):
    from accounts.models import User
    from accounts.discord_api import get_currently_playing, refresh_access_token
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    if not user.discord_id or not user.discord_polling_enabled or not user.discord_access_token:
        return

    result = get_currently_playing(user.discord_access_token)

    # Refresh token if needed
    if result is None and user.discord_refresh_token:
        tokens = refresh_access_token(user.discord_refresh_token)
        if tokens and 'access_token' in tokens:
            user.discord_access_token = tokens['access_token']
            user.discord_refresh_token = tokens.get('refresh_token', user.discord_refresh_token)
            user.save()
            result = get_currently_playing(user.discord_access_token)

    _handle_presence(user, result['name'] if result else None, Session.SOURCE_DISCORD)


def schedule_discord_polling():
    from accounts.models import User
    _schedule_all(
        User.objects.filter(discord_polling_enabled=True).exclude(discord_id=''),
        'accounts.tasks.poll_discord_for_user'
    )


# ─── XBOX ─────────────────────────────────────────────────────────────────────

def poll_xbox_for_user(user_id):
    from accounts.models import User
    from accounts.xbox_api import get_fresh_xsts, get_currently_playing
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    if not user.xbox_id or not user.xbox_polling_enabled or not user.xbox_access_token:
        return

    xsts_token, uhs = get_fresh_xsts(user)
    if not xsts_token:
        return

    result = get_currently_playing(xsts_token, uhs)
    _handle_presence(user, result['name'] if result else None, Session.SOURCE_XBOX)


def schedule_xbox_polling():
    from accounts.models import User
    _schedule_all(
        User.objects.filter(xbox_polling_enabled=True).exclude(xbox_id=''),
        'accounts.tasks.poll_xbox_for_user'
    )


# ─── PSN ──────────────────────────────────────────────────────────────────────

def poll_psn_for_user(user_id):
    from accounts.models import User
    from accounts.psn_api import get_currently_playing
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    if not user.psn_username or not user.psn_polling_enabled:
        return

    result = get_currently_playing(user.psn_username)
    _handle_presence(user, result['name'] if result else None, Session.SOURCE_PSN)


def schedule_psn_polling():
    from accounts.models import User
    _schedule_all(
        User.objects.filter(psn_polling_enabled=True).exclude(psn_username=''),
        'accounts.tasks.poll_psn_for_user'
    )