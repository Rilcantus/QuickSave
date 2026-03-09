import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def build_system_prompt(user, game):
    """Build the system prompt with the user's game context and journal notes."""
    from django.db.models import Sum
    from games.views import format_duration

    sessions = game.sessions.filter(ended_at__isnull=False)
    total_seconds = sessions.aggregate(total=Sum('duration_seconds'))['total'] or 0
    session_count = sessions.count()

    journal_entries = game.journal_entries.order_by('-created_at')[:5]

    lines = [
        "You are an AI gaming assistant inside QuickSave, a gaming journal app.",
        f"You are helping {user.username} with {game.title}"
        + (f" on {game.platform}" if game.platform else "") + ".",
        "",
        "Their gameplay stats:",
        f"- Sessions played: {session_count}",
        f"- Total playtime: {format_duration(total_seconds)}",
    ]

    if game.status:
        lines.append(f"- Status: {game.get_status_display()}")
    if game.rating:
        lines.append(f"- Personal rating: {game.rating}/10")

    if journal_entries:
        lines.append("")
        lines.append("Their recent journal entries (most recent first):")
        for entry in journal_entries:
            lines.append(f"\n[{entry.created_at.strftime('%b %d, %Y')}]")
            if entry.body:
                lines.append(f"Notes: {entry.body[:400]}")
            if entry.accomplishments:
                lines.append(f"Accomplishments: {entry.accomplishments[:200]}")
            if entry.blockers:
                lines.append(f"Blockers/frustrations: {entry.blockers[:200]}")
            if entry.next_goals:
                lines.append(f"Next goals: {entry.next_goals[:200]}")
            if entry.mood:
                lines.append(f"Mood: {entry.mood}")

    lines += [
        "",
        "Be conversational, helpful, and concise. Reference their notes when relevant.",
        "Help with tips, builds, walkthroughs, strategy, lore, or anything game-related.",
        "Keep responses focused and practical — avoid walls of text.",
    ]

    return "\n".join(lines)


def chat(user, game, message, history):
    """
    Send a message to Claude with the user's game context.
    history: list of {role, content} dicts (prior turns)
    Returns the assistant's reply string, or raises an exception on error.
    """
    if not getattr(settings, 'ANTHROPIC_API_KEY', ''):
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    system_prompt = build_system_prompt(user, game)
    messages = list(history) + [{"role": "user", "content": message}]

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )

    return response.content[0].text
