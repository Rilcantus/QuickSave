from play_sessions.models import Session


def active_session(request):
    if not request.user.is_authenticated:
        return {}
    
    session = Session.objects.filter(
        game__user=request.user,
        ended_at__isnull=True
    ).select_related('game').first()
    
    return {'active_session': session}