import urllib.request
import urllib.parse
import json
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def get_oauth_url():
    """Generate Microsoft OAuth URL for Xbox Live."""
    params = urllib.parse.urlencode({
        'client_id': settings.MICROSOFT_CLIENT_ID,
        'redirect_uri': settings.MICROSOFT_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'XboxLive.signin XboxLive.offline_access offline_access',
        'response_mode': 'query',
    })
    url = f"https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?{params}"
    print(f"Xbox OAuth URL: {url}")
    return url


def exchange_code(code):
    """Exchange OAuth code for Microsoft access token."""
    data = urllib.parse.urlencode({
        'client_id': settings.MICROSOFT_CLIENT_ID,
        'client_secret': settings.MICROSOFT_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.MICROSOFT_REDIRECT_URI,
        'scope': 'XboxLive.signin XboxLive.offline_access offline_access',
    }).encode()

    req = urllib.request.Request(
        'https://login.microsoftonline.com/consumers/oauth2/v2.0/token',
        data=data,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'QuickSave/1.0'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Xbox token exchange error: {e}")
        return None


def refresh_access_token(refresh_token):
    """Refresh an expired Microsoft access token."""
    data = urllib.parse.urlencode({
        'client_id': settings.MICROSOFT_CLIENT_ID,
        'client_secret': settings.MICROSOFT_CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'scope': 'XboxLive.signin XboxLive.offline_access offline_access',
    }).encode()

    req = urllib.request.Request(
        'https://login.microsoftonline.com/consumers/oauth2/v2.0/token',
        data=data,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'QuickSave/1.0'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Xbox token refresh error: {e}")
        return None


def get_xsts_token(ms_access_token):
    """
    Exchange Microsoft access token for Xbox Live XSTS token.
    Two step process: first get user token, then exchange for XSTS.
    """
    # Step 1: Get Xbox user token
    user_token_data = json.dumps({
        "Properties": {
            "AuthMethod": "RPS",
            "SiteName": "user.auth.xboxlive.com",
            "RpsTicket": f"d={ms_access_token}"
        },
        "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT"
    }).encode()

    req = urllib.request.Request(
        'https://user.auth.xboxlive.com/user/authenticate',
        data=user_token_data,
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'QuickSave/1.0'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            user_token_resp = json.loads(response.read().decode())
            user_token = user_token_resp.get('Token')
            uhs = user_token_resp.get('DisplayClaims', {}).get('xui', [{}])[0].get('uhs')
    except Exception as e:
        print(f"Xbox user token error: {e}")
        return None, None

    if not user_token:
        return None, None

    # Step 2: Exchange for XSTS token
    xsts_data = json.dumps({
        "Properties": {
            "SandboxId": "RETAIL",
            "UserTokens": [user_token]
        },
        "RelyingParty": "http://xboxlive.com",
        "TokenType": "JWT"
    }).encode()

    req = urllib.request.Request(
        'https://xsts.auth.xboxlive.com/xsts/authorize',
        data=xsts_data,
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'QuickSave/1.0'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xsts_resp = json.loads(response.read().decode())
            xsts_token = xsts_resp.get('Token')
            return xsts_token, uhs
    except Exception as e:
        print(f"Xbox XSTS token error: {e}")
        return None, None


def get_xbox_profile(xsts_token, uhs):
    """Get Xbox Live profile (gamertag, avatar, XUID)."""
    auth_header = f'XBL3.0 x={uhs};{xsts_token}'
    req = urllib.request.Request(
        'https://profile.xboxlive.com/users/me/profile/settings?settings=Gamertag,GameDisplayPicRaw',
        headers={
            'Authorization': auth_header,
            'x-xbl-contract-version': '2',
            'Accept': 'application/json',
            'User-Agent': 'QuickSave/1.0'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            user = data.get('profileUsers', [{}])[0]
            xuid = user.get('id', '')
            settings_list = user.get('settings', [])
            gamertag = ''
            avatar = ''
            for s in settings_list:
                if s.get('id') == 'Gamertag':
                    gamertag = s.get('value', '')
                elif s.get('id') == 'GameDisplayPicRaw':
                    avatar = s.get('value', '')
            return {'xuid': xuid, 'gamertag': gamertag, 'avatar': avatar}
    except Exception as e:
        print(f"Xbox profile error: {e}")
        return None


def get_currently_playing(xsts_token, uhs):
    """
    Get the game the user is currently playing on Xbox.
    Uses the presence endpoint.
    Returns dict with game name or None.
    """

    XBOX_IGNORE_TITLES = {'online', 'home', 'dashboard', 'xbox app'}

    auth_header = f'XBL3.0 x={uhs};{xsts_token}'
    req = urllib.request.Request(
        'https://userpresence.xboxlive.com/users/me?level=all',
        headers={
            'Authorization': auth_header,
            'x-xbl-contract-version': '3',
            'Accept': 'application/json',
            'User-Agent': 'QuickSave/1.0'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            # Check if user is in a game
            state = data.get('state', '')
            if state != 'Online':
                return None
            devices = data.get('devices', [])
            for device in devices:
                    titles = device.get('titles', [])
                    for title in titles:
                        name = title.get('name', '')
                        if title.get('placement') == 'Full' and name.lower() not in XBOX_IGNORE_TITLES:
                            return {
                                'name': name,
                                'title_id': title.get('id', ''),
                                'device': device.get('type', ''),
                            }
            return None
    except Exception as e:
        print(f"Xbox presence error: {e}")
        return None


def get_fresh_xsts(user):
    from django.utils import timezone

    # Check if access token needs refresh
    if user.xbox_token_expires and timezone.now() >= user.xbox_token_expires:
        if not user.xbox_refresh_token:
            return None, None
        tokens = refresh_access_token(user.xbox_refresh_token)
        if not tokens:
            return None, None
        user.xbox_access_token = tokens['access_token']
        user.xbox_refresh_token = tokens.get('refresh_token', user.xbox_refresh_token)
        expires_in = tokens.get('expires_in', 3600)
        user.xbox_token_expires = timezone.now() + timedelta(seconds=expires_in)
        user.save()

    return get_xsts_token(user.xbox_access_token)