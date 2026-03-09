import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from play_sessions.models import Session
from .rawg import search_games
from .models import Game, CustomFieldDefinition, Descriptor
from .forms import GameForm, CustomFieldDefinitionForm

logger = logging.getLogger(__name__)


def _safe_json(data):
    """Serialize to JSON with HTML-unsafe characters escaped for inline <script> use."""
    return json.dumps(data).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def format_duration(seconds):
    if not seconds:
        return '0m'
    hours, remainder = divmod(int(seconds), 3600)
    minutes = remainder // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def build_weekly_chart(sessions, num_weeks=8):
    """Return (labels, counts, hours) lists for the last num_weeks weeks."""
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    labels, counts, hours = [], [], []
    for i in range(num_weeks - 1, -1, -1):
        week_start = now - timedelta(weeks=i + 1)
        week_end = now - timedelta(weeks=i)
        week_qs = sessions.filter(started_at__gte=week_start, started_at__lt=week_end)
        labels.append((now - timedelta(weeks=i)).strftime('%b %d'))
        counts.append(week_qs.count())
        secs = week_qs.aggregate(total=Sum('duration_seconds'))['total'] or 0
        hours.append(round(secs / 3600, 1))
    return labels, counts, hours


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
    sessions = game.sessions.select_related('descriptor').order_by('-started_at')[:10]
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

AI_FREE_LIMIT = 3


@login_required
def ai_assistant(request, pk):
    from django.utils import timezone
    from .models import AIUsageLog
    game = get_object_or_404(Game, pk=pk, user=request.user)
    if request.user.is_pro:
        ai_limit = None
        ai_uses_today = 0
    else:
        today = timezone.now().date()
        log = AIUsageLog.objects.filter(user=request.user, date=today).first()
        ai_uses_today = log.count if log else 0
        ai_limit = AI_FREE_LIMIT
    return render(request, 'games/ai_assistant.html', {
        'game': game,
        'ai_uses_today': ai_uses_today,
        'ai_limit': ai_limit,
    })


@login_required
def ai_chat(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.utils import timezone
    from .models import AIUsageLog

    # IP-level rate limit — 60 requests/hour regardless of account
    try:
        from ratelimit.utils import is_ratelimited
        limited = is_ratelimited(request, group='ai_chat', key='ip', rate='60/h', increment=True)
        if limited:
            return JsonResponse({'error': 'Too many requests. Please slow down.'}, status=429)
    except Exception:
        pass

    game = get_object_or_404(Game, pk=pk, user=request.user)
    today = timezone.now().date()

    # Check daily limit for free users
    if not request.user.is_pro:
        log, _ = AIUsageLog.objects.get_or_create(
            user=request.user, date=today, defaults={'count': 0}
        )
        if log.count >= AI_FREE_LIMIT:
            return JsonResponse({
                'error': f"You've used all {AI_FREE_LIMIT} free AI questions for today. Upgrade to Pro for unlimited access.",
                'limit_reached': True,
            }, status=429)
    else:
        log = None

    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        history = data.get('history', [])
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if not message:
        return JsonResponse({'error': 'Message required'}, status=400)

    # Sanitize history to only allowed roles/keys
    clean_history = [
        {'role': m['role'], 'content': m['content']}
        for m in history
        if isinstance(m, dict) and m.get('role') in ('user', 'assistant')
        and isinstance(m.get('content'), str)
    ][-20:]

    try:
        from .ai_assistant import chat
        reply = chat(request.user, game, message, clean_history)
    except Exception as e:
        logger.error("AI chat error for game %s: %s", pk, e)
        return JsonResponse({'error': 'Failed to get a response. Please try again.'}, status=500)

    # Increment usage counter for free users
    remaining = None
    if not request.user.is_pro and log is not None:
        AIUsageLog.objects.filter(pk=log.pk).update(count=log.count + 1)
        remaining = max(0, AI_FREE_LIMIT - (log.count + 1))

    return JsonResponse({'reply': reply, 'remaining': remaining})


@login_required
def rawg_search(request):
    from ratelimit.decorators import ratelimit
    from ratelimit.exceptions import Ratelimited
    query = request.GET.get('q', '').strip()
    # 30 searches per hour per user
    try:
        from ratelimit.utils import is_ratelimited
        limited = is_ratelimited(request, group='rawg_search', key='user', rate='30/h', increment=True)
        if limited:
            return JsonResponse({'error': 'Too many searches. Try again in an hour.'}, status=429)
    except Exception:
        pass
    results = search_games(query)
    return JsonResponse({'results': results})

@login_required
def game_stats(request, pk):
    from django.db.models import Sum, Avg, Max, Count

    game = get_object_or_404(Game, pk=pk, user=request.user)
    sessions = game.sessions.filter(ended_at__isnull=False)

    total_seconds = sessions.aggregate(total=Sum('duration_seconds'))['total'] or 0
    avg_seconds = sessions.aggregate(avg=Avg('duration_seconds'))['avg'] or 0
    max_seconds = sessions.aggregate(max=Max('duration_seconds'))['max'] or 0
    total_sessions = sessions.count()
    total_entries = game.journal_entries.count()

    weeks, week_counts, week_durations = build_weekly_chart(sessions)

    top_descriptors = sessions.filter(
        descriptor__isnull=False
    ).values('descriptor__name').annotate(
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
    from django.db.models import Sum

    games = request.user.games.all()
    sessions = Session.objects.filter(
        game__user=request.user,
        ended_at__isnull=False
    )

    total_seconds = sessions.aggregate(total=Sum('duration_seconds'))['total'] or 0
    total_sessions = sessions.count()
    total_entries = request.user.journal_entries.count()
    total_games = games.count()

    weeks, week_counts, week_durations = build_weekly_chart(sessions)

    time_per_game = games.annotate(
        total_time=Sum('sessions__duration_seconds')
    ).filter(total_time__isnull=False).order_by('-total_time')[:6]

    return render(request, 'games/overall_stats.html', {
        'total_playtime': format_duration(total_seconds),
        'total_sessions': total_sessions,
        'total_entries': total_entries,
        'total_games': total_games,
        'weeks_json': json.dumps(weeks),
        'week_counts_json': json.dumps(week_counts),
        'week_durations_json': json.dumps(week_durations),
        'game_names_json': _safe_json([g.title for g in time_per_game]),
        'game_times_json': json.dumps([round((g.total_time or 0) / 3600, 1) for g in time_per_game]),
        'time_per_game': time_per_game,
    })


@login_required
def gaming_wrapped(request, year=None):
    from django.db.models import Sum, Max, Count
    from django.utils import timezone
    from collections import Counter

    if not request.user.is_pro:
        return render(request, 'games/wrapped_upgrade.html')

    current_year = timezone.now().year
    if year is None:
        year = current_year

    # Available years with session data
    available_years = list(
        Session.objects.filter(game__user=request.user, ended_at__isnull=False)
        .dates('started_at', 'year')
        .values_list('started_at__year', flat=True)
        .order_by('-started_at__year')
        .distinct()
    )
    if not available_years:
        available_years = [current_year]
    if year not in available_years:
        year = available_years[0]

    sessions = Session.objects.filter(
        game__user=request.user,
        ended_at__isnull=False,
        started_at__year=year,
    )

    total_seconds = sessions.aggregate(total=Sum('duration_seconds'))['total'] or 0
    total_sessions = sessions.count()
    total_games = sessions.values('game').distinct().count()
    total_entries = request.user.journal_entries.filter(created_at__year=year).count()

    # Top 5 games by playtime
    top_games = (
        sessions.values('game__id', 'game__title', 'game__cover_image_url')
        .annotate(total_time=Sum('duration_seconds'), session_count=Count('id'))
        .order_by('-total_time')[:5]
    )

    # Most active month
    month_data = (
        sessions.values('started_at__month')
        .annotate(hours=Sum('duration_seconds'))
        .order_by('started_at__month')
    )
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_labels = [month_names[m['started_at__month'] - 1] for m in month_data]
    month_hours = [round((m['hours'] or 0) / 3600, 1) for m in month_data]
    peak_month = month_names[max(month_data, key=lambda m: m['hours'] or 0)['started_at__month'] - 1] if month_data else None

    # Longest single session
    longest = sessions.order_by('-duration_seconds').select_related('game').first()

    # Favorite platform (by session count)
    source_counts = dict(
        sessions.values('source').annotate(count=Count('id')).values_list('source', 'count')
    )
    fav_source = max(source_counts, key=source_counts.get) if source_counts else None
    source_labels = {
        'manual': 'Manual', 'steam': 'Steam', 'xbox': 'Xbox',
        'discord': 'Discord', 'psn': 'PSN', 'roblox': 'Roblox',
    }

    # Mood breakdown from journal entries
    moods = list(
        request.user.journal_entries.filter(created_at__year=year)
        .exclude(mood='')
        .values_list('mood', flat=True)
    )
    mood_counts = Counter(moods)
    top_mood = mood_counts.most_common(1)[0][0] if mood_counts else None

    # First game of the year
    first_session = sessions.order_by('started_at').select_related('game').first()

    return render(request, 'games/gaming_wrapped.html', {
        'year': year,
        'current_year': current_year,
        'available_years': available_years,
        'total_playtime': format_duration(total_seconds),
        'total_hours': round(total_seconds / 3600, 1),
        'total_sessions': total_sessions,
        'total_games': total_games,
        'total_entries': total_entries,
        'top_games': top_games,
        'month_labels_json': json.dumps(month_labels),
        'month_hours_json': json.dumps(month_hours),
        'peak_month': peak_month,
        'longest': longest,
        'fav_source': source_labels.get(fav_source, fav_source) if fav_source else None,
        'mood_counts': dict(mood_counts.most_common(5)),
        'top_mood': top_mood,
        'first_session': first_session,
    })