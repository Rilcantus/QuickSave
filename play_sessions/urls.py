from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from . import views


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


@login_required
def dashboard(request):
    from games.models import Game
    from .models import Session
    from journal.models import JournalEntry

    games = Game.objects.filter(user=request.user)
    active_sessions = Session.objects.filter(
        game__user=request.user,
        ended_at__isnull=True
    ).select_related('game', 'descriptor')

    recent_sessions = Session.objects.filter(
        game__user=request.user,
        ended_at__isnull=False
    ).select_related('game', 'descriptor').order_by('-ended_at')[:5]

    recent_entries = JournalEntry.objects.filter(
        user=request.user
    ).select_related('session__game', 'game').order_by('-created_at')[:5]

    return render(request, 'dashboard.html', {
        'games': games,
        'active_sessions': active_sessions,
        'recent_sessions': recent_sessions,
        'recent_entries': recent_entries,
    })


urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('games/<int:game_pk>/start/', views.session_start, name='session_start'),
    path('sessions/<int:pk>/active/', views.session_active, name='session_active'),
    path('sessions/<int:pk>/done/', views.session_end_prompt, name='session_end_prompt'),
    path('sessions/', views.session_history, name='session_history'),
]