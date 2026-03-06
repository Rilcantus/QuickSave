from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .forms import RegisterForm, LoginForm, UpdateProfileForm


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