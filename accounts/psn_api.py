from django.conf import settings


def get_psn_client():
    """Get an authenticated PSNAWP client using the service account token."""
    from psnawp_api import PSNAWP
    return PSNAWP(settings.PSN_NPSSO_TOKEN)


def get_psn_profile(psn_username):
    """
    Look up a PSN user's profile and account ID by username.
    Returns dict with id, username, avatar or None on failure.
    """
    try:
        client = get_psn_client()
        user = client.user(online_id=psn_username)
        profile = user.profile()
        return {
            'id': user.account_id,
            'username': profile.get('onlineId', psn_username),
            'avatar': profile.get('avatars', [{}])[0].get('url', ''),
        }
    except Exception:
        return None


def get_currently_playing(psn_username):
    """
    Get the game a PSN user is currently playing.
    Returns dict with name or None if not playing / profile private.
    """
    try:
        client = get_psn_client()
        user = client.user(online_id=psn_username)
        presence = user.get_presence()

        availability = presence.get('basicPresence', {}).get('availability', '')
        if availability != 'availableToPlay':
            return None

        game_title_info = presence.get('basicPresence', {}).get('gameTitleInfoList', [])
        if not game_title_info:
            return None

        game = game_title_info[0]
        name = game.get('titleName', '')

        if not name:
            return None

        return {'name': name}

    except Exception:
        return None