from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .forms import RegisterForm, LoginForm, UpdateProfileForm


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to QuickSave, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Please fix the errors below.")

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def account_settings(request):
    return render(request, 'accounts/settings.html')


@login_required
def update_profile(request):
    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
            return redirect('account_settings')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = UpdateProfileForm(instance=request.user)

    return render(request, 'accounts/update_profile.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully!")
            return redirect('account_settings')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = PasswordChangeForm(request.user)

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

@login_required
def steam_connect(request):
    if request.method == 'POST':
        from .steam import get_player_summary, resolve_steam_id
        steam_input = request.POST.get('steam_id', '').strip()

        if not steam_input:
            messages.error(request, "Please enter a Steam ID or username.")
            return redirect('account_settings')

        # Try as vanity URL first, then as direct Steam ID
        steam_id = None
        if steam_input.isdigit() and len(steam_input) == 17:
            steam_id = steam_input
        else:
            steam_id = resolve_steam_id(steam_input)

        if not steam_id:
            messages.error(request, "Couldn't find that Steam account. Try your 17-digit Steam ID instead.")
            return redirect('steam_settings')

        # Verify the account exists and get profile info
        player = get_player_summary(steam_id)
        if not player:
            messages.error(request, "Couldn't connect to Steam. Check your ID and try again.")
            return redirect('steam_settings')

        request.user.steam_id = steam_id
        request.user.steam_username = player.get('personaname', '')
        request.user.steam_avatar = player.get('avatarmedium', '')
        request.user.steam_polling_enabled = True
        request.user.save()

        # Set up polling schedule
        from .cron import setup_steam_polling_schedule
        setup_steam_polling_schedule()

        messages.success(request, f"Connected to Steam as {request.user.steam_username}!")
        return redirect('steam_settings')

    return redirect('steam_settings')


@login_required
def steam_disconnect(request):
    if request.method == 'POST':
        request.user.steam_id = ''
        request.user.steam_username = ''
        request.user.steam_avatar = ''
        request.user.steam_polling_enabled = False
        request.user.save()
        messages.success(request, "Steam account disconnected.")
    return redirect('account_settings')


@login_required
def steam_settings(request):
    from .steam import get_recently_played
    recently_played = []
    if request.user.steam_id:
        recently_played = get_recently_played(request.user.steam_id)[:5]

    return render(request, 'accounts/steam_settings.html', {
        'recently_played': recently_played,
    })


@login_required  
def steam_toggle_polling(request):
    if request.method == 'POST':
        request.user.steam_polling_enabled = not request.user.steam_polling_enabled
        request.user.save()
        status = "enabled" if request.user.steam_polling_enabled else "paused"
        messages.success(request, f"Steam auto-tracking {status}.")
    return redirect('steam_settings')

@login_required
def steam_poll_now(request):
    if request.method == 'POST':
        if request.user.steam_id:
            from .tasks import poll_steam_for_user
            poll_steam_for_user(request.user.pk)
            messages.success(request, "Steam status checked!")
        # Redirect back to wherever the user came from
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'dashboard'
        return redirect(next_url)
    return redirect('dashboard')

@login_required
def discord_oauth(request):
    """Redirect to Discord OAuth."""
    from .discord_api import get_oauth_url
    from django.http import HttpResponseRedirect
    url = get_oauth_url()
    return HttpResponseRedirect(url)


def discord_callback(request):
    """Handle Discord OAuth callback."""
    from .discord_api import exchange_code, get_current_user
    from .cron import setup_discord_polling_schedule

    code = request.GET.get('code')
    error = request.GET.get('error')
    error_description = request.GET.get('error_description', '')

    if error or not code:
        messages.error(request, f"Discord error: {error} — {error_description}")
        return redirect('account_settings')

    # Exchange code for tokens
    tokens = exchange_code(code)
    if not tokens or 'access_token' not in tokens:
        messages.error(request, "Failed to connect Discord. Please try again.")
        return redirect('account_settings')

    # Get user profile
    user_data = get_current_user(tokens['access_token'])
    if not user_data:
        messages.error(request, "Failed to get Discord profile.")
        return redirect('account_settings')

    # Save to user
    request.user.discord_id = user_data.get('id', '')
    request.user.discord_username = user_data.get('username', '')
    avatar_hash = user_data.get('avatar', '')
    if avatar_hash:
        request.user.discord_avatar = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{avatar_hash}.png"
    request.user.discord_access_token = tokens['access_token']
    request.user.discord_refresh_token = tokens.get('refresh_token', '')
    request.user.discord_polling_enabled = True
    request.user.save()

    # Set up polling
    setup_discord_polling_schedule()

    messages.success(request, f"Connected to Discord as {request.user.discord_username}!")
    return redirect('discord_settings')


@login_required
def discord_disconnect(request):
    if request.method == 'POST':
        request.user.discord_id = ''
        request.user.discord_username = ''
        request.user.discord_avatar = ''
        request.user.discord_access_token = ''
        request.user.discord_refresh_token = ''
        request.user.discord_polling_enabled = False
        request.user.save()
        messages.success(request, "Discord account disconnected.")
    return redirect('account_settings')


@login_required
def discord_settings(request):
    return render(request, 'accounts/discord_settings.html')


@login_required
def discord_toggle_polling(request):
    if request.method == 'POST':
        request.user.discord_polling_enabled = not request.user.discord_polling_enabled
        request.user.save()
        status = "enabled" if request.user.discord_polling_enabled else "paused"
        messages.success(request, f"Discord auto-tracking {status}.")
    return redirect('discord_settings')

# ─── XBOX VIEWS ───────────────────────────────────────────────────────────────
# Add these to accounts/views.py

@login_required
def xbox_connect(request):
    """Redirect to Microsoft OAuth."""
    from .xbox_api import get_oauth_url
    from django.http import HttpResponseRedirect
    url = get_oauth_url()
    return HttpResponseRedirect(url)


def xbox_callback(request):
    """Handle Microsoft OAuth callback."""
    from .xbox_api import exchange_code, get_xsts_token, get_xbox_profile
    from django.utils import timezone
    from datetime import timedelta

    code = request.GET.get('code')
    error = request.GET.get('error')
    error_description = request.GET.get('error_description', '')

    if error or not code:
        messages.error(request, f"Xbox error: {error} — {error_description}")
        return redirect('account_settings')

    # Exchange code for Microsoft tokens
    tokens = exchange_code(code)
    if not tokens or 'access_token' not in tokens:
        messages.error(request, "Failed to connect Xbox. Please try again.")
        return redirect('account_settings')

    # Get XSTS token for Xbox Live API calls
    xsts_token, uhs = get_xsts_token(tokens['access_token'])
    if not xsts_token:
        messages.error(request, "Failed to authenticate with Xbox Live.")
        return redirect('account_settings')

    # Get Xbox profile
    profile = get_xbox_profile(xsts_token, uhs)
    if not profile:
        messages.error(request, "Failed to get Xbox profile.")
        return redirect('account_settings')

    # Save to user
    expires_in = tokens.get('expires_in', 3600)
    request.user.xbox_id = profile.get('xuid', '')
    request.user.xbox_gamertag = profile.get('gamertag', '')
    request.user.xbox_avatar = profile.get('avatar', '')
    request.user.xbox_access_token = tokens['access_token']
    request.user.xbox_refresh_token = tokens.get('refresh_token', '')
    request.user.xbox_token_expires = timezone.now() + timedelta(seconds=expires_in)
    request.user.xbox_polling_enabled = True
    request.user.save()

    messages.success(request, f"Connected to Xbox as {request.user.xbox_gamertag}!")
    return redirect('xbox_settings')


@login_required
def xbox_disconnect(request):
    if request.method == 'POST':
        request.user.xbox_id = ''
        request.user.xbox_gamertag = ''
        request.user.xbox_avatar = ''
        request.user.xbox_access_token = ''
        request.user.xbox_refresh_token = ''
        request.user.xbox_token_expires = None
        request.user.xbox_polling_enabled = False
        request.user.save()
        messages.success(request, "Xbox account disconnected.")
    return redirect('account_settings')


@login_required
def xbox_settings(request):
    return render(request, 'accounts/xbox_settings.html')


@login_required
def xbox_toggle_polling(request):
    if request.method == 'POST':
        request.user.xbox_polling_enabled = not request.user.xbox_polling_enabled
        request.user.save()
        status = "enabled" if request.user.xbox_polling_enabled else "paused"
        messages.success(request, f"Xbox auto-tracking {status}.")
    return redirect('xbox_settings')


@login_required
def xbox_poll_now(request):
    """Manually trigger an Xbox presence check."""
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
        if playing:
            messages.success(request, f"Xbox: Currently playing {playing['name']}")
        else:
            messages.info(request, "Xbox: Not currently playing anything.")

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))