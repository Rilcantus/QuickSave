from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from games.models import Game
from play_sessions.models import Session
from journal.models import JournalEntry


# ── Auth ──────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def api_token(request):
    """POST { username, password } → { token, username }"""
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    if not username or not password:
        return Response({'error': 'username and password required'}, status=400)

    user = authenticate(request, username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=401)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'username': user.username})


# ── Games ─────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_games(request):
    """GET → [{ id, title, platform, cover_image_url }]"""
    games = Game.objects.filter(user=request.user).order_by('title')
    data = [
        {
            'id': g.pk,
            'title': g.title,
            'platform': g.platform or '',
            'cover_image_url': g.cover_image_url or '',
        }
        for g in games
    ]
    return Response(data)


# ── Sessions ──────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_active_session(request):
    """GET → active session object or 404"""
    session = Session.objects.filter(
        game__user=request.user,
        ended_at__isnull=True,
    ).select_related('game').first()

    if not session:
        return Response({'detail': 'No active session'}, status=404)

    return Response({
        'id': session.pk,
        'game_id': session.game.pk,
        'game_title': session.game.title,
        'started_at': session.started_at.isoformat(),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_start_session(request):
    """POST { game_id } → session object"""
    game_id = request.data.get('game_id')
    if not game_id:
        return Response({'error': 'game_id required'}, status=400)

    try:
        game = Game.objects.get(pk=game_id, user=request.user)
    except Game.DoesNotExist:
        return Response({'error': 'Game not found'}, status=404)

    # End any existing active session for this user first
    Session.objects.filter(
        game__user=request.user,
        ended_at__isnull=True,
    ).update(ended_at=timezone.now())

    session = Session.objects.create(game=game, source=Session.SOURCE_MANUAL)
    return Response({
        'id': session.pk,
        'game_id': game.pk,
        'game_title': game.title,
        'started_at': session.started_at.isoformat(),
    }, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_end_session(request, pk):
    """POST { notes } → ended session"""
    try:
        session = Session.objects.get(pk=pk, game__user=request.user)
    except Session.DoesNotExist:
        return Response({'error': 'Session not found'}, status=404)

    if not session.is_active:
        return Response({'error': 'Session already ended'}, status=400)

    notes = request.data.get('notes', '')
    session.notes = notes
    session.end()

    return Response({
        'id': session.pk,
        'game_title': session.game.title,
        'duration_display': session.duration_display,
        'notes': session.notes,
    })


# ── Quick notes ───────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_quick_note(request):
    """POST { game_id, text } → saves a standalone journal entry"""
    game_id = request.data.get('game_id')
    text = request.data.get('text', '').strip()

    if not game_id or not text:
        return Response({'error': 'game_id and text required'}, status=400)

    try:
        game = Game.objects.get(pk=game_id, user=request.user)
    except Game.DoesNotExist:
        return Response({'error': 'Game not found'}, status=404)

    # Check if there's an active session to attach to
    active_session = Session.objects.filter(
        game=game,
        ended_at__isnull=True,
    ).first()

    entry = JournalEntry.objects.create(
        user=request.user,
        game=game,
        session=active_session,
        body=text,
    )

    return Response({'id': entry.pk, 'saved': True}, status=201)
