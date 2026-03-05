from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from games.models import Game
from .models import Session
from .forms import SessionStartForm, SessionEndForm


@login_required
def session_start(request, game_pk):
    game = get_object_or_404(Game, pk=game_pk, user=request.user)

    # Check if there's already an active session for this game
    active = Session.objects.filter(game=game, ended_at__isnull=True).first()
    if active:
        messages.warning(request, f"You already have an active session for {game.title}!")
        return redirect('session_active', pk=active.pk)

    form = SessionStartForm(game=game, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            session = form.save()
            messages.success(request, f"Session started for {game.title}!")
            return redirect('session_active', pk=session.pk)

    return render(request, 'play_sessions/session_start.html', {
        'game': game,
        'form': form,
    })


@login_required
def session_active(request, pk):
    session = get_object_or_404(Session, pk=pk, game__user=request.user)

    if not session.is_active:
        return redirect('game_detail', pk=session.game.pk)

    form = SessionEndForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            session.notes = form.cleaned_data.get('notes', '')
            session.end()
            messages.success(request, f"Session ended! {session.duration_display} played.")
            return redirect('session_end_prompt', pk=session.pk)

    return render(request, 'play_sessions/session_active.html', {
        'session': session,
        'form': form,
    })


@login_required
def session_end_prompt(request, pk):
    """Ask the user if they want to journal after ending a session."""
    session = get_object_or_404(Session, pk=pk, game__user=request.user)

    if session.is_active:
        return redirect('session_active', pk=session.pk)

    return render(request, 'play_sessions/session_end_prompt.html', {
        'session': session,
    })