from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Game
from .forms import GameForm


@login_required
def game_list(request):
    games = Game.objects.filter(user=request.user)
    return render(request, 'games/game_list.html', {'games': games})


@login_required
def game_create(request):
    form = GameForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            game = form.save(commit=False)
            game.user = request.user
            game.save()
            messages.success(request, f"'{game.title}' added to your library!")
            return redirect('game_detail', pk=game.pk)
        else:
            messages.error(request, "Please fix the errors below.")

    return render(request, 'games/game_form.html', {'form': form, 'action': 'Add Game'})


@login_required
def game_detail(request, pk):
    game = get_object_or_404(Game, pk=pk, user=request.user)
    sessions = game.sessions.all()[:10]
    journal_entries = game.journal_entries.all()[:5]
    return render(request, 'games/game_detail.html', {
        'game': game,
        'sessions': sessions,
        'journal_entries': journal_entries,
    })

@login_required
def game_edit(request, pk):
    game = get_object_or_404(Game, pk=pk, user=request.user)
    form = GameForm(request.POST or None, instance=game)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f"'{game.title}' updated!")
            return redirect('game_detail', pk=game.pk)

    return render(request, 'games/game_form.html', {'form': form, 'action': 'Edit Game', 'game': game})


@login_required
def game_delete(request, pk):
    game = get_object_or_404(Game, pk=pk, user=request.user)
    if request.method == 'POST':
        title = game.title
        game.delete()
        messages.success(request, f"'{title}' deleted.")
        return redirect('game_list')

    return render(request, 'games/game_confirm_delete.html', {'game': game})