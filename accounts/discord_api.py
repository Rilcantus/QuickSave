import urllib.request
import urllib.parse
import urllib.error
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def get_oauth_url():
    """Generate Discord OAuth URL."""
    params = urllib.parse.urlencode({
        'client_id': settings.DISCORD_CLIENT_ID,
        'redirect_uri': settings.DISCORD_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'identify',
    })
    return f"https://discord.com/api/oauth2/authorize?{params}"


def exchange_code(code):
    """Exchange OAuth code for access token."""
    data = urllib.parse.urlencode({
        'client_id': settings.DISCORD_CLIENT_ID,
        'client_secret': settings.DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.DISCORD_REDIRECT_URI,
    }).encode()

    req = urllib.request.Request(
        'https://discord.com/api/oauth2/token',
        data=data,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'QuickSave/1.0',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        logger.warning("Discord token exchange failed: %s", e)
        return None
    except json.JSONDecodeError as e:
        logger.warning("Discord token exchange returned invalid JSON: %s", e)
        return None


def refresh_access_token(refresh_token):
    """Refresh an expired access token."""
    data = urllib.parse.urlencode({
        'client_id': settings.DISCORD_CLIENT_ID,
        'client_secret': settings.DISCORD_CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }).encode()

    req = urllib.request.Request(
        'https://discord.com/api/oauth2/token',
        data=data,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'QuickSave/1.0',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        logger.warning("Discord token refresh failed: %s", e)
        return None
    except json.JSONDecodeError as e:
        logger.warning("Discord token refresh returned invalid JSON: %s", e)
        return None


def get_current_user(access_token):
    """Get Discord user profile."""
    req = urllib.request.Request(
        'https://discord.com/api/users/@me',
        headers={
            'Authorization': f'Bearer {access_token}',
            'User-Agent': 'QuickSave/1.0',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        logger.warning("Discord get_current_user failed: %s", e)
        return None
    except json.JSONDecodeError as e:
        logger.warning("Discord get_current_user returned invalid JSON: %s", e)
        return None


def get_user_activities(access_token):
    """
    Get current user activities including game playing status.
    Note: requires activities.read scope and user must have
    activity status sharing enabled in Discord privacy settings.
    """
    req = urllib.request.Request(
        'https://discord.com/api/users/@me/activities',
        headers={
            'Authorization': f'Bearer {access_token}',
            'User-Agent': 'QuickSave/1.0',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        logger.warning("Discord get_user_activities failed: %s", e)
        return None
    except json.JSONDecodeError as e:
        logger.warning("Discord get_user_activities returned invalid JSON: %s", e)
        return None


def get_currently_playing(access_token):
    """
    Get the game the user is currently playing via Discord.
    Returns dict with game name or None.
    """
    activities = get_user_activities(access_token)
    if not activities:
        return None

    # Activity type 0 = Playing a game
    for activity in activities:
        if activity.get('type') == 0:
            return {
                'name': activity.get('name', ''),
                'details': activity.get('details', ''),
                'state': activity.get('state', ''),
            }
    return None
