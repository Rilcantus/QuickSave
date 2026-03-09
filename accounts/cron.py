_SCHEDULES = [
    ('Steam Polling',   'accounts.tasks.schedule_steam_polling'),
    ('Discord Polling', 'accounts.tasks.schedule_discord_polling'),
    ('Xbox Polling',    'accounts.tasks.schedule_xbox_polling'),
    ('PSN Polling',     'accounts.tasks.schedule_psn_polling'),
    ('Roblox Polling',  'accounts.tasks.schedule_roblox_polling'),
]


def setup_all_polling_schedules():
    """Set up all platform polling schedules at 5-minute intervals."""
    from django_q.models import Schedule
    for name, func in _SCHEDULES:
        Schedule.objects.get_or_create(
            name=name,
            defaults={
                'func': func,
                'schedule_type': Schedule.MINUTES,
                'minutes': 5,
            }
        )


# Individual entry points kept for backwards compatibility
def setup_steam_polling_schedule():
    setup_all_polling_schedules()

def setup_discord_polling_schedule():
    setup_all_polling_schedules()

def setup_xbox_polling_schedule():
    setup_all_polling_schedules()

def setup_psn_polling_schedule():
    setup_all_polling_schedules()

def setup_roblox_polling_schedule():
    setup_all_polling_schedules()
