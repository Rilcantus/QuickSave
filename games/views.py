from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from play_sessions.models import Session
from .rawg import search_games
from .models import Game, CustomFieldDefinition, Descriptor
from .forms import GameForm, CustomFieldDefinitionForm


@login_required
def game_list(request):
    query = request.GET.get('q', '').strip()
    games = Game.objects.filter(user=request.user)
    if query:
        games = games.filter(title__icontains=query)
    return render(request, 'games/game_list.html', {
        'games': games,
        'query': query,
    })

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

    from django.db.models import Sum
    total_seconds = game.sessions.filter(
        ended_at__isnull=False
    ).aggregate(total=Sum('duration_seconds'))['total'] or 0

    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    if hours > 0:
        total_playtime = f"{hours}h {minutes}m"
    elif minutes > 0:
        total_playtime = f"{minutes}m"
    else:
        total_playtime = "0m"

    return render(request, 'games/game_detail.html', {
        'game': game,
        'sessions': sessions,
        'journal_entries': journal_entries,
        'total_playtime': total_playtime,
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

@login_required
def custom_field_create(request, game_pk):
    game = get_object_or_404(Game, pk=game_pk, user=request.user)
    form = CustomFieldDefinitionForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            field = form.save(commit=False)
            field.game = game
            field.order = game.custom_field_definitions.count()
            field.save()
            messages.success(request, f"Field '{field.name}' added!")
            return redirect('game_detail', pk=game.pk)

    return render(request, 'games/custom_field_form.html', {
        'form': form,
        'game': game,
    })


@login_required
def custom_field_delete(request, pk):
    field = get_object_or_404(CustomFieldDefinition, pk=pk, game__user=request.user)
    game = field.game
    if request.method == 'POST':
        field.delete()
        messages.success(request, f"Field deleted.")
        return redirect('game_detail', pk=game.pk)

    return render(request, 'games/custom_field_confirm_delete.html', {
        'field': field,
        'game': game,
    })

@login_required
def descriptor_detail(request, game_pk, pk):
    game = get_object_or_404(Game, pk=game_pk, user=request.user)
    descriptor = get_object_or_404(Descriptor, pk=pk, game=game)
    sessions = descriptor.sessions.all()
    return render(request, 'games/descriptor_detail.html', {
        'game': game,
        'descriptor': descriptor,
        'sessions': sessions,
    })

@login_required
def descriptor_edit(request, game_pk, pk):
    game = get_object_or_404(Game, pk=game_pk, user=request.user)
    descriptor = get_object_or_404(Descriptor, pk=pk, game=game)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            descriptor.name = name
            descriptor.save()
            messages.success(request, f"Run renamed to '{name}'!")
            return redirect('game_detail', pk=game.pk)
        else:
            messages.error(request, "Name can't be empty.")

    return render(request, 'games/descriptor_form.html', {
        'game': game,
        'descriptor': descriptor,
    })

@login_required
def descriptor_delete(request, game_pk, pk):
    game = get_object_or_404(Game, pk=game_pk, user=request.user)
    descriptor = get_object_or_404(Descriptor, pk=pk, game=game)

    if request.method == 'POST':
        name = descriptor.name
        descriptor.delete()
        messages.success(request, f"'{name}' deleted.")
        return redirect('game_detail', pk=game.pk)

    return render(request, 'games/descriptor_confirm_delete.html', {
        'game': game,
        'descriptor': descriptor,
    })

@login_required
def rawg_search(request):
    query = request.GET.get('q', '').strip()
    results = search_games(query)
    return JsonResponse({'results': results})

@login_required
def game_stats(request, pk):
    from django.db.models import Sum, Avg, Max, Count
    from datetime import timedelta
    from django.utils import timezone
    import json

    game = get_object_or_404(Game, pk=pk, user=request.user)
    sessions = game.sessions.filter(ended_at__isnull=False)

    # Core stats
    total_seconds = sessions.aggregate(total=Sum('duration_seconds'))['total'] or 0
    avg_seconds = sessions.aggregate(avg=Avg('duration_seconds'))['avg'] or 0
    max_seconds = sessions.aggregate(max=Max('duration_seconds'))['max'] or 0
    total_sessions = sessions.count()
    total_entries = game.journal_entries.count()

    def format_duration(seconds):
        if not seconds:
            return '0m'
        hours, remainder = divmod(int(seconds), 3600)
        minutes = remainder // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    # Sessions per week (last 8 weeks)
    weeks = []
    week_counts = []
    week_durations = []
    for i in range(7, -1, -1):
        week_start = timezone.now() - timedelta(weeks=i+1)
        week_end = timezone.now() - timedelta(weeks=i)
        week_sessions = sessions.filter(
            started_at__gte=week_start,
            started_at__lt=week_end
        )
        label = (timezone.now() - timedelta(weeks=i)).strftime('%b %d')
        weeks.append(label)
        week_counts.append(week_sessions.count())
        week_secs = week_sessions.aggregate(total=Sum('duration_seconds'))['total'] or 0
        week_durations.append(round(week_secs / 3600, 1))

    # Top run labels
    top_descriptors = sessions.filter(
        descriptor__isnull=False
    ).values(
        'descriptor__name'
    ).annotate(
        count=Count('id'),
        total_time=Sum('duration_seconds')
    ).order_by('-count')[:5]

    return render(request, 'games/game_stats.html', {
        'game': game,
        'total_playtime': format_duration(total_seconds),
        'avg_session': format_duration(avg_seconds),
        'longest_session': format_duration(max_seconds),
        'total_sessions': total_sessions,
        'total_entries': total_entries,
        'weeks_json': json.dumps(weeks),
        'week_counts_json': json.dumps(week_counts),
        'week_durations_json': json.dumps(week_durations),
        'top_descriptors': top_descriptors,
    })


@login_required
def overall_stats(request):
    from django.db.models import Sum, Avg, Max, Count
    from datetime import timedelta
    from django.utils import timezone
    import json

    games = request.user.games.all()
    sessions = Session.objects.filter(
        game__user=request.user,
        ended_at__isnull=False
    )

    # Core stats
    total_seconds = sessions.aggregate(total=Sum('duration_seconds'))['total'] or 0
    total_sessions = sessions.count()
    total_entries = request.user.journal_entries.count()
    total_games = games.count()

    def format_duration(seconds):
        if not seconds:
            return '0m'
        hours, remainder = divmod(int(seconds), 3600)
        minutes = remainder // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    # Sessions per week (last 8 weeks)
    weeks = []
    week_counts = []
    week_durations = []
    for i in range(7, -1, -1):
        week_start = timezone.now() - timedelta(weeks=i+1)
        week_end = timezone.now() - timedelta(weeks=i)
        week_sessions = sessions.filter(
            started_at__gte=week_start,
            started_at__lt=week_end
        )
        label = (timezone.now() - timedelta(weeks=i)).strftime('%b %d')
        weeks.append(label)
        week_counts.append(week_sessions.count())
        week_secs = week_sessions.aggregate(total=Sum('duration_seconds'))['total'] or 0
        week_durations.append(round(week_secs / 3600, 1))

    # Time per game
    time_per_game = games.annotate(
        total_time=Sum('sessions__duration_seconds')
    ).filter(
        total_time__isnull=False
    ).order_by('-total_time')[:6]

    game_names = json.dumps([g.title for g in time_per_game])
    game_times = json.dumps([
        round((g.total_time or 0) / 3600, 1) for g in time_per_game
    ])

    return render(request, 'games/overall_stats.html', {
        'total_playtime': format_duration(total_seconds),
        'total_sessions': total_sessions,
        'total_entries': total_entries,
        'total_games': total_games,
        'weeks_json': json.dumps(weeks),
        'week_counts_json': json.dumps(week_counts),
        'week_durations_json': json.dumps(week_durations),
        'game_names_json': game_names,
        'game_times_json': game_times,
        'time_per_game': time_per_game,
    })