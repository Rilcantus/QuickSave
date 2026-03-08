import urllib.request
import urllib.parse
import urllib.error
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def search_games(query):
    """Search RAWG API for games matching query."""
    if not query or not settings.RAWG_API_KEY:
        return []

    params = urllib.parse.urlencode({
        'key': settings.RAWG_API_KEY,
        'search': query,
        'page_size': 6,
        'search_precise': True,
    })

    url = f"https://api.rawg.io/api/games?{params}"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'QuickSave/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            results = []
            for game in data.get('results', []):
                results.append({
                    'name': game.get('name', ''),
                    'image': game.get('background_image', ''),
                    'released': game.get('released', ''),
                    'rating': game.get('rating', 0),
                    'slug': game.get('slug', ''),
                })
            return results
    except urllib.error.URLError as e:
        logger.warning("RAWG API request failed: %s", e)
        return []
    except json.JSONDecodeError as e:
        logger.warning("RAWG API returned invalid JSON: %s", e)
        return []