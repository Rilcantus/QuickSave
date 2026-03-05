from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from play_sessions.models import Session
from games.models import Game
from .models import JournalEntry
from .forms import JournalEntryForm


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
    entries = JournalEntry.objects.filter(
        user=request.user
    ).select_related(
        'game', 'session__game', 'session__descriptor'
    ).order_by('-created_at')

    # Group by game in Python instead of using regroup template tag
    from collections import defaultdict
    groups = defaultdict(list)
    for entry in entries:
        game = entry.get_game
        if game:
            groups[game].append(entry)

    # Convert to list of tuples for template
    grouped_entries = [(game, entries) for game, entries in groups.items()]

    return render(request, 'journal/journal_list.html', {
        'entries': entries,
        'grouped_entries': grouped_entries,
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