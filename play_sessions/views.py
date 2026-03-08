from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from games.models import Game
from journal.models import JournalEntry
from .models import Session
from .forms import SessionStartForm, SessionEndForm


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


@login_required
def dashboard(request):
    games = Game.objects.filter(user=request.user).annotate(
        session_count=Count('sessions')
    )
    active_sessions = Session.objects.filter(
        game__user=request.user,
        ended_at__isnull=True
    ).select_related('game', 'descriptor')

    recent_sessions = Session.objects.filter(
        game__user=request.user,
        ended_at__isnull=False
    ).select_related('game', 'descriptor').prefetch_related(
        'custom_field_values__field_definition'
    ).order_by('-ended_at')[:5]

    recent_entries = JournalEntry.objects.filter(
        user=request.user
    ).select_related('session__game', 'game').order_by('-created_at')[:5]

    return render(request, 'dashboard.html', {
        'games': games,
        'active_sessions': active_sessions,
        'recent_sessions': recent_sessions,
        'recent_entries': recent_entries,
    })


@login_required
def session_start(request, game_pk):
    game = get_object_or_404(Game, pk=game_pk, user=request.user)

    active = Session.objects.filter(game=game, ended_at__isnull=True).first()
    if active:
        messages.warning(request, f"You already have an active session for {game.title}!")
        return redirect('session_active', pk=active.pk)

    # Get custom field definitions and last values for auto-fill
    field_definitions = game.custom_field_definitions.all()
    last_session = game.sessions.filter(ended_at__isnull=False).first()
    last_values = {}
    if last_session:
        for val in last_session.custom_field_values.select_related('field_definition'):
            last_values[val.field_definition_id] = val.value

    field_data = []
    for field in field_definitions:
        field_data.append({
            'definition': field,
            'last_value': last_values.get(field.pk, ''),
        })

    form = SessionStartForm(game=game, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            session = form.save()
            # Save custom field values
            for item in field_data:
                field_def = item['definition']
                value = request.POST.get(f'custom_field_{field_def.pk}', '').strip()
                if value:
                    from play_sessions.models import CustomFieldValue
                    from games.models import CustomFieldChoice
                    CustomFieldValue.objects.create(
                        session=session,
                        field_definition=field_def,
                        value=value
                    )
                    if field_def.field_type == 'choice':
                        CustomFieldChoice.objects.get_or_create(
                            field_definition=field_def,
                            value=value
                        )
            messages.success(request, f"Session started for {game.title}!")
            return redirect('session_active', pk=session.pk)

    return render(request, 'play_sessions/session_start.html', {
        'game': game,
        'form': form,
        'field_data': field_data,
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

@login_required
def session_history(request):
    from games.models import Game
    from django.core.paginator import Paginator

    sessions = Session.objects.filter(
        game__user=request.user,
        ended_at__isnull=False
    ).select_related('game', 'descriptor').order_by('-started_at')

    game_filter = request.GET.get('game')
    games = Game.objects.filter(user=request.user)
    if game_filter:
        sessions = sessions.filter(game__pk=game_filter)

    paginator = Paginator(sessions, 20)
    page = request.GET.get('page', 1)
    sessions_page = paginator.get_page(page)

    return render(request, 'play_sessions/session_history.html', {
        'sessions': sessions_page,
        'games': games,
        'game_filter': game_filter,
        'paginator': paginator,
    })