from django.utils import timezone
from accounts.steam import get_currently_playing
from games.models import Game
from games.rawg import search_games
from play_sessions.models import Session


def poll_steam_for_user(user_id):
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

        if active_session and active_session.game.title.lower() == game_name.lower():
            return

        # Only end session if Steam owns it
        if active_session and active_session.source == Session.SOURCE_STEAM:
            active_session.end()
        elif active_session:
            # Another platform owns it — don't touch it
            return

        game = Game.objects.filter(user=user, title__iexact=game_name).first()
        if not game:
            game = Game(user=user, title=game_name)
            results = search_games(game_name)
            if results and results[0]['image']:
                game.cover_image_url = results[0]['image']
            game.save()

        Session.objects.create(
            game=game,
            started_at=timezone.now(),
            source=Session.SOURCE_STEAM,
        )

    else:
        # Only end session if Steam owns it
        if active_session and active_session.source == Session.SOURCE_STEAM:
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

    currently_playing = get_currently_playing(user.discord_access_token)

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

        if active_session and active_session.game.title.lower() == game_name.lower():
            return

        # Only end session if Discord owns it
        if active_session and active_session.source == Session.SOURCE_DISCORD:
            active_session.end()
        elif active_session:
            # Another platform owns it — don't touch it


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

def poll_xbox_for_user(user_id):
    from accounts.models import User
    from accounts.xbox_api import get_fresh_xsts, get_currently_playing

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    if not user.xbox_id or not user.xbox_polling_enabled:
        return

    if not user.xbox_access_token:
        return

    xsts_token, uhs = get_fresh_xsts(user)
    if not xsts_token:
        return

    currently_playing = get_currently_playing(xsts_token, uhs)

    active_session = Session.objects.filter(
        game__user=user,
        ended_at__isnull=True
    ).select_related('game').first()

    if currently_playing:
        game_name = currently_playing['name']

        if active_session and active_session.game.title.lower() == game_name.lower():
            return

        # Only end session if Xbox owns it
        if active_session and active_session.source == Session.SOURCE_XBOX:
            active_session.end()
        elif active_session:
            # Another platform owns it — don't touch it
            return

        game = Game.objects.filter(user=user, title__iexact=game_name).first()
        if not game:
            game = Game(user=user, title=game_name)
            results = search_games(game_name)
            if results and results[0]['image']:
                game.cover_image_url = results[0]['image']
            game.save()

        Session.objects.create(
            game=game,
            started_at=timezone.now(),
            source=Session.SOURCE_XBOX,
        )

    else:
        # Only end session if Xbox owns it
        if active_session and active_session.source == Session.SOURCE_XBOX:
            active_session.end()


def schedule_xbox_polling():
    """Schedule polling for all users with Xbox connected."""
    from accounts.models import User
    from django_q.tasks import async_task

    users = User.objects.filter(
        xbox_polling_enabled=True,
        xbox_id__isnull=False
    ).exclude(xbox_id='')

    for user in users:
        async_task('accounts.tasks.poll_xbox_for_user', user.pk)