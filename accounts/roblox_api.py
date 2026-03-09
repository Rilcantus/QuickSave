import logging
import requests

logger = logging.getLogger(__name__)

_USERS_URL = 'https://users.roblox.com/v1/usernames/users'
_PRESENCE_URL = 'https://presence.roblox.com/v1/presence/users'
_AVATAR_URL = 'https://thumbnails.roblox.com/v1/users/avatar-headshot'

# userPresenceType values
_PRESENCE_IN_GAME = 2


def get_roblox_profile(username):
    """
    Resolve a Roblox username to user ID and avatar.
    Returns dict with id, username, avatar or None on failure.
    """
    try:
        resp = requests.post(
            _USERS_URL,
            json={'usernames': [username], 'excludeBannedUsers': True},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get('data', [])
        if not data:
            return None

        user = data[0]
        user_id = user['id']
        display_name = user.get('name', username)

        # Fetch headshot avatar
        avatar_url = ''
        try:
            av_resp = requests.get(
                _AVATAR_URL,
                params={'userIds': user_id, 'size': '150x150', 'format': 'Png', 'isCircular': 'false'},
                timeout=10,
            )
            av_resp.raise_for_status()
            av_data = av_resp.json().get('data', [])
            if av_data:
                avatar_url = av_data[0].get('imageUrl', '')
        except Exception:
            pass

        return {
            'id': str(user_id),
            'username': display_name,
            'avatar': avatar_url,
        }
    except Exception as e:
        logger.warning("Roblox profile lookup failed for %s: %s", username, e)
        return None


def get_currently_playing(roblox_user_id):
    """
    Get the game a Roblox user is currently playing.
    Returns dict with name or None if not in a game.
    """
    try:
        resp = requests.post(
            _PRESENCE_URL,
            json={'userIds': [int(roblox_user_id)]},
            timeout=10,
        )
        resp.raise_for_status()
        presences = resp.json().get('userPresences', [])
        if not presences:
            return None

        presence = presences[0]
        if presence.get('userPresenceType') != _PRESENCE_IN_GAME:
            return None

        game_name = presence.get('lastLocation', '').strip()
        return {'name': game_name} if game_name else None

    except Exception as e:
        logger.warning("Roblox presence lookup failed for user_id %s: %s", roblox_user_id, e)
        return None
