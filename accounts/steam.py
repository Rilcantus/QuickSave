import urllib.request
import urllib.parse
import urllib.error
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def get_player_summary(steam_id):
    """Get basic Steam profile info."""
    params = urllib.parse.urlencode({
        'key': settings.STEAM_API_KEY,
        'steamids': steam_id,
    })
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?{params}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'QuickSave/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            players = data.get('response', {}).get('players', [])
            return players[0] if players else None
    except urllib.error.URLError as e:
        logger.warning("Steam API request failed: %s", e)
        return None
    except json.JSONDecodeError as e:
        logger.warning("Steam API returned invalid JSON: %s", e)
        return None


def get_currently_playing(steam_id):
    """Get the game the user is currently playing, or None."""
    player = get_player_summary(steam_id)
    if not player:
        return None

    game_id = player.get('gameid')
    game_name = player.get('gameextrainfo')

    if game_id and game_name:
        return {
            'steam_app_id': game_id,
            'name': game_name,
        }
    return None


def get_recently_played(steam_id):
    """Get recently played games."""
    params = urllib.parse.urlencode({
        'key': settings.STEAM_API_KEY,
        'steamid': steam_id,
        'count': 10,
    })
    url = f"https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/?{params}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'QuickSave/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get('response', {}).get('games', [])
    except urllib.error.URLError as e:
        logger.warning("Steam recently played request failed: %s", e)
        return []
    except json.JSONDecodeError as e:
        logger.warning("Steam recently played returned invalid JSON: %s", e)
        return []


def resolve_steam_id(vanity_url):
    """Convert a Steam vanity URL name to a Steam ID."""
    params = urllib.parse.urlencode({
        'key': settings.STEAM_API_KEY,
        'vanityurl': vanity_url,
    })
    url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?{params}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'QuickSave/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            result = data.get('response', {})
            if result.get('success') == 1:
                return result.get('steamid')
    except urllib.error.URLError as e:
        logger.warning("Steam vanity URL resolve failed: %s", e)
    except json.JSONDecodeError as e:
        logger.warning("Steam vanity URL returned invalid JSON: %s", e)
    return None
