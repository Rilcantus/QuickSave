from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .forms import RegisterForm, LoginForm, UpdateProfileForm


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _disconnect_platform(user, fields):
    """Clear a set of fields on the user model."""
    for field, value in fields.items():
        setattr(user, field, value)
    user.save()


def _toggle_polling(user, field):
    """Toggle a boolean polling field and return new status string."""
    current = getattr(user, field)
    setattr(user, field, not current)
    user.save()
    return "enabled" if not current else "paused"


# ─── PUBLIC VIEWS ─────────────────────────────────────────────────────────────

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome to QuickSave, {user.username}!")
        return redirect('onboarding')
    elif request.method == 'POST':
        messages.error(request, "Please fix the errors below.")
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def onboarding(request):
    user = request.user
    has_game = user.games.exists()
    has_platform = any([
        user.steam_id,
        user.xbox_id,
        user.psn_username,
        user.discord_id,
        user.roblox_username,
    ])
    if has_game and has_platform:
        return redirect('dashboard')
    return render(request, 'accounts/onboarding.html', {
        'has_game': has_game,
        'has_platform': has_platform,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, f"Welcome back, {form.get_user().username}!")
        return redirect('home')
    elif request.method == 'POST':
        messages.error(request, "Invalid username or password.")
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── ACCOUNT SETTINGS ─────────────────────────────────────────────────────────

@login_required
def account_settings(request):
    return render(request, 'accounts/settings.html')


@login_required
def update_profile(request):
    form = UpdateProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profile updated!")
        return redirect('account_settings')
    elif request.method == 'POST':
        messages.error(request, "Please fix the errors below.")
    return render(request, 'accounts/update_profile.html', {'form': form})


@login_required
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        update_session_auth_hash(request, form.save())
        messages.success(request, "Password changed successfully!")
        return redirect('account_settings')
    elif request.method == 'POST':
        messages.error(request, "Please fix the errors below.")
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect('home')
    return render(request, 'accounts/delete_account.html')


# ─── STEAM ────────────────────────────────────────────────────────────────────

@login_required
def steam_settings(request):
    from .steam import get_recently_played
    recently_played = get_recently_played(request.user.steam_id)[:5] if request.user.steam_id else []
    return render(request, 'accounts/steam_settings.html', {'recently_played': recently_played})


@login_required
def steam_connect(request):
    if request.method == 'POST':
        from .steam import get_player_summary, resolve_steam_id
        steam_input = request.POST.get('steam_id', '').strip()
        if not steam_input:
            messages.error(request, "Please enter a Steam ID or username.")
            return redirect('account_settings')

        steam_id = steam_input if (steam_input.isdigit() and len(steam_input) == 17) else resolve_steam_id(steam_input)
        if not steam_id:
            messages.error(request, "Couldn't find that Steam account. Try entering your 17-digit Steam ID (find it at steamid.io) or make sure your profile is set to Public.")
            return redirect('steam_settings')

        player = get_player_summary(steam_id)
        if not player:
            messages.error(request, "Found your Steam ID but couldn't load your profile. Make sure your Steam profile and game details are set to Public in Steam → Settings → Privacy.")
            return redirect('steam_settings')

        request.user.steam_id = steam_id
        request.user.steam_username = player.get('personaname', '')
        request.user.steam_avatar = player.get('avatarmedium', '')
        request.user.steam_polling_enabled = True
        request.user.save()

        from .cron import setup_steam_polling_schedule
        setup_steam_polling_schedule()
        messages.success(request, f"Connected to Steam as {request.user.steam_username}!")
    return redirect('steam_settings')


@login_required
def steam_disconnect(request):
    if request.method == 'POST':
        _disconnect_platform(request.user, {
            'steam_id': '', 'steam_username': '',
            'steam_avatar': '', 'steam_polling_enabled': False,
        })
        messages.success(request, "Steam account disconnected.")
    return redirect('account_settings')


@login_required
def steam_toggle_polling(request):
    if request.method == 'POST':
        status = _toggle_polling(request.user, 'steam_polling_enabled')
        messages.success(request, f"Steam auto-tracking {status}.")
    return redirect('steam_settings')


@login_required
def steam_poll_now(request):
    if request.method == 'POST' and request.user.steam_id:
        from .tasks import poll_steam_for_user
        poll_steam_for_user(request.user.pk)
        messages.success(request, "Steam status checked!")
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'dashboard'
    return redirect(next_url)


# ─── DISCORD ──────────────────────────────────────────────────────────────────

@login_required
def discord_settings(request):
    return render(request, 'accounts/discord_settings.html')


@login_required
def discord_oauth(request):
    from .discord_api import get_oauth_url
    from django.http import HttpResponseRedirect
    return HttpResponseRedirect(get_oauth_url())


def discord_callback(request):
    from .discord_api import exchange_code, get_current_user
    from .cron import setup_discord_polling_schedule

    code = request.GET.get('code')
    error = request.GET.get('error')
    if error or not code:
        messages.error(request, f"Discord authorization was cancelled or failed ({error}). Please try connecting again.")
        return redirect('discord_settings')

    tokens = exchange_code(code)
    if not tokens or 'access_token' not in tokens:
        messages.error(request, "Failed to connect Discord — the authorization code expired. Please try connecting again.")
        return redirect('discord_settings')

    user_data = get_current_user(tokens['access_token'])
    if not user_data:
        messages.error(request, "Connected to Discord but couldn't load your profile. Please try again.")
        return redirect('discord_settings')

    avatar_hash = user_data.get('avatar', '')
    request.user.discord_id = user_data.get('id', '')
    request.user.discord_username = user_data.get('username', '')
    request.user.discord_avatar = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{avatar_hash}.png" if avatar_hash else ''
    request.user.discord_access_token = tokens['access_token']
    request.user.discord_refresh_token = tokens.get('refresh_token', '')
    request.user.discord_polling_enabled = True
    request.user.save()

    setup_discord_polling_schedule()
    messages.success(request, f"Connected to Discord as {request.user.discord_username}!")
    return redirect('discord_settings')


@login_required
def discord_disconnect(request):
    if request.method == 'POST':
        _disconnect_platform(request.user, {
            'discord_id': '', 'discord_username': '', 'discord_avatar': '',
            'discord_access_token': '', 'discord_refresh_token': '',
            'discord_polling_enabled': False,
        })
        messages.success(request, "Discord account disconnected.")
    return redirect('account_settings')


@login_required
def discord_toggle_polling(request):
    if request.method == 'POST':
        status = _toggle_polling(request.user, 'discord_polling_enabled')
        messages.success(request, f"Discord auto-tracking {status}.")
    return redirect('discord_settings')


# ─── XBOX ─────────────────────────────────────────────────────────────────────

@login_required
def xbox_settings(request):
    return render(request, 'accounts/xbox_settings.html')


@login_required
def xbox_connect(request):
    from .xbox_api import get_oauth_url
    from django.http import HttpResponseRedirect
    return HttpResponseRedirect(get_oauth_url())


def xbox_callback(request):
    from .xbox_api import exchange_code, get_xsts_token, get_xbox_profile
    from .cron import setup_xbox_polling_schedule
    from django.utils import timezone
    from datetime import timedelta

    code = request.GET.get('code')
    error = request.GET.get('error')
    if error or not code:
        messages.error(request, f"Xbox authorization was cancelled or failed ({error}). Please try connecting again.")
        return redirect('xbox_settings')

    tokens = exchange_code(code)
    if not tokens or 'access_token' not in tokens:
        messages.error(request, "Failed to connect Xbox — the authorization code expired. Please try connecting again.")
        return redirect('xbox_settings')

    xsts_token, uhs = get_xsts_token(tokens['access_token'])
    if not xsts_token:
        messages.error(request, "Failed to authenticate with Xbox Live. Make sure your Microsoft account has an active Xbox profile and try again.")
        return redirect('xbox_settings')

    profile = get_xbox_profile(xsts_token, uhs)
    if not profile:
        messages.error(request, "Connected to Xbox Live but couldn't load your profile. Please try reconnecting.")
        return redirect('xbox_settings')

    request.user.xbox_id = profile.get('xuid', '')
    request.user.xbox_gamertag = profile.get('gamertag', '')
    request.user.xbox_avatar = profile.get('avatar', '')
    request.user.xbox_access_token = tokens['access_token']
    request.user.xbox_refresh_token = tokens.get('refresh_token', '')
    request.user.xbox_token_expires = timezone.now() + timedelta(seconds=tokens.get('expires_in', 3600))
    request.user.xbox_polling_enabled = True
    request.user.save()

    setup_xbox_polling_schedule()
    messages.success(request, f"Connected to Xbox as {request.user.xbox_gamertag}!")
    return redirect('xbox_settings')


@login_required
def xbox_disconnect(request):
    if request.method == 'POST':
        _disconnect_platform(request.user, {
            'xbox_id': '', 'xbox_gamertag': '', 'xbox_avatar': '',
            'xbox_access_token': '', 'xbox_refresh_token': '',
            'xbox_token_expires': None, 'xbox_polling_enabled': False,
        })
        messages.success(request, "Xbox account disconnected.")
    return redirect('account_settings')


@login_required
def xbox_toggle_polling(request):
    if request.method == 'POST':
        status = _toggle_polling(request.user, 'xbox_polling_enabled')
        messages.success(request, f"Xbox auto-tracking {status}.")
    return redirect('xbox_settings')


@login_required
def xbox_poll_now(request):
    if request.method == 'POST':
        from .xbox_api import get_fresh_xsts, get_currently_playing
        if not request.user.xbox_id:
            messages.error(request, "No Xbox account connected.")
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        xsts_token, uhs = get_fresh_xsts(request.user)
        if not xsts_token:
            messages.error(request, "Failed to refresh Xbox token.")
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        playing = get_currently_playing(xsts_token, uhs)
        msg = f"Xbox: Currently playing {playing['name']}" if playing else "Xbox: Not currently playing anything."
        messages.success(request, msg) if playing else messages.info(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


# ─── PSN ──────────────────────────────────────────────────────────────────────

@login_required
def psn_settings(request):
    return render(request, 'accounts/psn_settings.html')


@login_required
def psn_connect(request):
    if request.method == 'POST':
        from .psn_api import get_psn_profile
        psn_username = request.POST.get('psn_username', '').strip()
        if psn_username:
            profile = get_psn_profile(psn_username)
            if profile:
                request.user.psn_username = profile['username']
                request.user.psn_account_id = profile['id']
                request.user.psn_avatar = profile.get('avatar', '').replace('http://', 'https://', 1)
                request.user.psn_polling_enabled = True
                request.user.save()
                from .cron import setup_psn_polling_schedule
                setup_psn_polling_schedule()
                messages.success(request, f"Connected as {profile['username']}!")
            else:
                messages.error(request, "PSN username not found or profile is private. Make sure your PSN Online ID is correct and your profile is set to Public in PlayStation Network → Privacy Settings.")
    return redirect('psn_settings')


@login_required
def psn_disconnect(request):
    if request.method == 'POST':
        _disconnect_platform(request.user, {
            'psn_username': '', 'psn_account_id': '',
            'psn_avatar': '', 'psn_polling_enabled': False,
        })
        messages.success(request, "PSN disconnected.")
    return redirect('psn_settings')


@login_required
def psn_toggle_polling(request):
    if request.method == 'POST':
        status = _toggle_polling(request.user, 'psn_polling_enabled')
        messages.success(request, f"PSN auto-tracking {status}.")
    return redirect('psn_settings')


@login_required
def psn_poll_now(request):
    if request.method == 'POST' and request.user.psn_username:
        from .psn_api import get_currently_playing
        result = get_currently_playing(request.user.psn_username)
        if result:
            messages.success(request, f"Currently playing: {result['name']}")
        else:
            messages.info(request, "Not currently playing anything on PSN.")
    return redirect('psn_settings')


# ─── SYNC ALL ─────────────────────────────────────────────────────────────────

@login_required
def sync_all(request):
    if request.method != 'POST':
        return redirect('dashboard')

    from concurrent.futures import ThreadPoolExecutor, as_completed
    from play_sessions.models import Session
    from .tasks import (
        poll_steam_for_user, poll_xbox_for_user,
        poll_psn_for_user, poll_discord_for_user,
        poll_roblox_for_user,
    )

    active = Session.objects.filter(
        game__user=request.user, ended_at__isnull=True
    ).select_related('game').first()
    if active:
        messages.info(request, f"Already tracking: {active.game.title}")
        return redirect('session_active', pk=active.pk)

    u = request.user
    polls = {}
    if u.steam_id and u.steam_polling_enabled:
        polls['Steam'] = poll_steam_for_user
    if u.xbox_id and u.xbox_polling_enabled:
        polls['Xbox'] = poll_xbox_for_user
    if u.psn_username and u.psn_polling_enabled:
        polls['PSN'] = poll_psn_for_user
    if u.discord_id and u.discord_polling_enabled:
        polls['Discord'] = poll_discord_for_user
    if u.roblox_user_id and u.roblox_polling_enabled:
        polls['Roblox'] = poll_roblox_for_user

    if not polls:
        messages.info(request, "No platforms connected with auto-tracking enabled.")
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'dashboard'
        return redirect(next_url)

    with ThreadPoolExecutor(max_workers=len(polls)) as executor:
        futures = {executor.submit(fn, u.pk): name for name, fn in polls.items()}
        for future in as_completed(futures):
            future.result()  # surface any exceptions

    active = Session.objects.filter(
        game__user=request.user, ended_at__isnull=True
    ).select_related('game').first()

    if active:
        messages.success(request, f"Session started: {active.game.title}!")
        return redirect('session_active', pk=active.pk)

    messages.info(request, f"Checked {', '.join(polls)} — not playing anything right now.")
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'dashboard'
    return redirect(next_url)


# ─── DATA EXPORT ──────────────────────────────────────────────────────────────

@login_required
def export_data(request):
    import json
    from django.http import HttpResponse
    from games.models import Game
    from play_sessions.models import Session
    from journal.models import JournalEntry

    user = request.user

    games = []
    for game in Game.objects.filter(user=user).prefetch_related('sessions', 'journal_entries'):
        games.append({
            'title': game.title,
            'platform': game.platform or '',
            'added': game.created_at.isoformat() if hasattr(game, 'created_at') else '',
        })

    sessions = []
    for s in Session.objects.filter(game__user=user).select_related('game', 'descriptor').order_by('-started_at'):
        sessions.append({
            'game': s.game.title,
            'descriptor': s.descriptor.name if s.descriptor else '',
            'started_at': s.started_at.isoformat(),
            'ended_at': s.ended_at.isoformat() if s.ended_at else None,
            'duration_seconds': s.duration_seconds,
            'notes': s.notes or '',
            'source': s.source,
        })

    entries = []
    for e in JournalEntry.objects.filter(user=user).select_related('session__game', 'game').order_by('-created_at'):
        game = e.get_game()
        entries.append({
            'game': game.title if game else '',
            'created_at': e.created_at.isoformat(),
            'body': e.body or '',
            'accomplishments': e.accomplishments or '',
            'blockers': e.blockers or '',
            'next_goals': e.next_goals or '',
            'mood': e.mood or '',
        })

    payload = {
        'exported_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        'username': user.username,
        'email': user.email,
        'games': games,
        'sessions': sessions,
        'journal_entries': entries,
    }

    response = HttpResponse(
        json.dumps(payload, indent=2),
        content_type='application/json',
    )
    response['Content-Disposition'] = f'attachment; filename="quicksave-export-{user.username}.json"'
    return response


# ─── ROBLOX ───────────────────────────────────────────────────────────────────

@login_required
def roblox_settings(request):
    return render(request, 'accounts/roblox_settings.html')


@login_required
def roblox_connect(request):
    if request.method == 'POST':
        from .roblox_api import get_roblox_profile
        roblox_username = request.POST.get('roblox_username', '').strip()
        if not roblox_username:
            messages.error(request, "Please enter a Roblox username.")
            return redirect('roblox_settings')

        profile = get_roblox_profile(roblox_username)
        if not profile:
            messages.error(request, "Roblox username not found. Make sure your username is spelled correctly and your profile is not banned.")
            return redirect('roblox_settings')

        request.user.roblox_username = profile['username']
        request.user.roblox_user_id = profile['id']
        request.user.roblox_avatar = profile.get('avatar', '')
        request.user.roblox_polling_enabled = True
        request.user.save()

        from .cron import setup_roblox_polling_schedule
        setup_roblox_polling_schedule()
        messages.success(request, f"Connected as {profile['username']}!")
    return redirect('roblox_settings')


@login_required
def roblox_disconnect(request):
    if request.method == 'POST':
        _disconnect_platform(request.user, {
            'roblox_username': '', 'roblox_user_id': '',
            'roblox_avatar': '', 'roblox_polling_enabled': False,
        })
        messages.success(request, "Roblox account disconnected.")
    return redirect('account_settings')


@login_required
def roblox_toggle_polling(request):
    if request.method == 'POST':
        status = _toggle_polling(request.user, 'roblox_polling_enabled')
        messages.success(request, f"Roblox auto-tracking {status}.")
    return redirect('roblox_settings')


@login_required
def roblox_poll_now(request):
    if request.method == 'POST' and request.user.roblox_user_id:
        from .roblox_api import get_currently_playing
        result = get_currently_playing(request.user.roblox_user_id)
        if result:
            messages.success(request, f"Currently playing: {result['name']}")
        else:
            messages.info(request, "Not currently in a Roblox game.")
    return redirect('roblox_settings')


# ─── PUSH NOTIFICATIONS ───────────────────────────────────────────────────────

@login_required
def push_subscribe(request):
    """Save a browser push subscription for the logged-in user."""
    import json as _json
    from django.http import JsonResponse
    from .models import PushSubscription

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = _json.loads(request.body)
        endpoint = data.get('endpoint', '').strip()
        keys = data.get('keys', {})
        p256dh = keys.get('p256dh', '').strip()
        auth = keys.get('auth', '').strip()
    except (ValueError, AttributeError):
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    if not endpoint or not p256dh or not auth:
        return JsonResponse({'error': 'Missing fields'}, status=400)

    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={'user': request.user, 'p256dh': p256dh, 'auth': auth},
    )
    return JsonResponse({'status': 'ok'})


@login_required
def push_unsubscribe(request):
    """Remove a push subscription."""
    import json as _json
    from django.http import JsonResponse
    from .models import PushSubscription

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = _json.loads(request.body)
        endpoint = data.get('endpoint', '').strip()
    except (ValueError, AttributeError):
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    return JsonResponse({'status': 'ok'})