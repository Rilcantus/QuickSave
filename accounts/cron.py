def setup_steam_polling_schedule():
    """Set up recurring Steam polling every 5 minutes."""
    from django_q.models import Schedule

    Schedule.objects.get_or_create(
        name='Steam Polling',
        defaults={
            'func': 'accounts.tasks.schedule_steam_polling',
            'schedule_type': Schedule.MINUTES,
            'minutes': 5,
        }
    )