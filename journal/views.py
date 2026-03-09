import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from play_sessions.models import Session
from games.models import Game
from .models import JournalEntry
from .forms import JournalEntryForm

logger = logging.getLogger(__name__)


@login_required
def journal_create_for_session(request, session_pk):
    session = get_object_or_404(Session, pk=session_pk, game__user=request.user)

    # If entry already exists, redirect to edit it
    if hasattr(session, 'journal_entry'):
        return redirect('journal_edit', pk=session.journal_entry.pk)

    form = JournalEntryForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.session = session
            entry.game = session.game
            entry.save()
            messages.success(request, "Journal entry saved! 💾")
            return redirect('journal_detail', pk=entry.pk)

    return render(request, 'journal/journal_form.html', {
        'form': form,
        'session': session,
        'game': session.game,
        'action': 'Write Entry',
    })


@login_required
def journal_create_standalone(request, game_pk):
    game = get_object_or_404(Game, pk=game_pk, user=request.user)

    form = JournalEntryForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.game = game
            entry.save()
            messages.success(request, "Journal entry saved! 💾")
            return redirect('journal_detail', pk=entry.pk)

    return render(request, 'journal/journal_form.html', {
        'form': form,
        'game': game,
        'action': 'Write Entry',
    })


@login_required
def journal_detail(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    return render(request, 'journal/journal_detail.html', {'entry': entry})


@login_required
def journal_list(request):
    query = request.GET.get('q', '').strip()
    entries = JournalEntry.objects.filter(
        user=request.user
    ).select_related(
        'game', 'session__game', 'session__descriptor'
    ).order_by('-created_at')

    if query:
        entries = entries.filter(
            models.Q(body__icontains=query) |
            models.Q(accomplishments__icontains=query) |
            models.Q(next_goals__icontains=query) |
            models.Q(session__game__title__icontains=query) |
            models.Q(game__title__icontains=query)
        )

    from collections import defaultdict
    groups = defaultdict(list)
    for entry in entries:
        game = entry.get_game
        if game:
            groups[game].append(entry)

    grouped_entries = [(game, entries) for game, entries in groups.items()]

    return render(request, 'journal/journal_list.html', {
        'entries': entries,
        'grouped_entries': grouped_entries,
        'query': query,
    })

@login_required
def journal_edit(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    form = JournalEntryForm(request.POST or None, instance=entry)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Entry updated!")
            return redirect('journal_detail', pk=entry.pk)

    return render(request, 'journal/journal_form.html', {
        'form': form,
        'entry': entry,
        'game': entry.get_game(),
        'action': 'Edit Entry',
    })


@login_required
def journal_delete(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        game = entry.get_game()
        entry.delete()
        messages.success(request, "Entry deleted.")
        return redirect('game_detail', pk=game.pk)

    return render(request, 'journal/journal_confirm_delete.html', {'entry': entry})


@login_required
def journal_ai_prefill(request, session_pk):
    """Return AI-generated journal draft for a session (Pro only)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if not request.user.is_pro:
        return JsonResponse({'error': 'Pro required'}, status=403)

    session = get_object_or_404(Session, pk=session_pk, game__user=request.user)

    from django.conf import settings
    if not getattr(settings, 'ANTHROPIC_API_KEY', ''):
        return JsonResponse({'error': 'AI unavailable'}, status=503)

    try:
        import anthropic
        from games.views import format_duration

        notes = session.notes or ''
        duration = session.duration_display or 'unknown duration'
        game = session.game

        system = (
            f"You are helping {request.user.username} write a gaming journal entry "
            f"for a {duration} session of {game.title}"
            + (f" on {game.platform}" if game.platform else "") + ".\n"
            "Based on their quick notes, generate a thoughtful journal entry draft.\n"
            "Return ONLY valid JSON with these keys: body, accomplishments, blockers, next_goals, mood.\n"
            "Keep each field concise (2-4 sentences max). mood should be 1-3 words.\n"
            "If there are no notes, make reasonable suggestions based on the game."
        )
        user_msg = f"Session notes: {notes}" if notes else f"No notes taken during this {duration} session of {game.title}."

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=512,
            system=system,
            messages=[{'role': 'user', 'content': user_msg}],
        )
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        draft = json.loads(text)
        return JsonResponse({
            'body': draft.get('body', ''),
            'accomplishments': draft.get('accomplishments', ''),
            'blockers': draft.get('blockers', ''),
            'next_goals': draft.get('next_goals', ''),
            'mood': draft.get('mood', ''),
        })
    except Exception as e:
        logger.error('Journal AI prefill error session %s: %s', session_pk, e)
        return JsonResponse({'error': 'Failed to generate draft.'}, status=500)