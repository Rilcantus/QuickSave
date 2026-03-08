# QuickSave — Project Context for Claude Code

## What is QuickSave?
A gaming journal and session tracking web app. Users can track their playtime across platforms, write journal entries after sessions, organize runs/playthroughs, and view stats. Built with the goal of being a full-featured app with eventual monetization.

**Live at:** https://www.quicksave.site
**Repo:** https://github.com/Rilcantus/QuickSave

---

## Tech Stack
- **Backend:** Django (Python)
- **Database:** PostgreSQL (Railway)
- **Frontend:** HTMX + Tailwind CSS (CDN)
- **Background Workers:** Django-Q
- **Hosting:** Railway (web service + worker service)
- **Domain:** GoDaddy → CNAME → Railway

---

## App Structure
```
config/          - Django settings, urls, wsgi
accounts/        - User model, auth, platform integrations
games/           - Game model, RAWG API cover art
play_sessions/   - Session model, session views
journal/         - Journal entry model and views
templates/       - All HTML templates
```

---

## User Model (accounts/models.py)
Custom user model with fields for each platform:

**Steam:** `steam_id`, `steam_username`, `steam_avatar`, `steam_polling_enabled`
**Xbox:** `xbox_id`, `xbox_gamertag`, `xbox_avatar`, `xbox_access_token`, `xbox_refresh_token`, `xbox_token_expires`, `xbox_polling_enabled`
**Discord:** `discord_id`, `discord_username`, `discord_avatar`, `discord_access_token`, `discord_refresh_token`, `discord_polling_enabled`
**PSN:** `psn_username`, `psn_account_id`, `psn_avatar`, `psn_polling_enabled`

---

## Platform Integrations
All platforms auto-detect what the user is playing and start/end sessions automatically via background polling every 5 minutes.

### Steam
- Uses Steam Web API with user's Steam ID
- Requires public profile + game activity visible
- File: `accounts/steam.py`

### Xbox
- Uses Microsoft OAuth2 → XSTS token exchange → Xbox Live API
- Azure App Registration required
- File: `accounts/xbox_api.py`

### Discord
- Uses Discord OAuth2 + Rich Presence API
- Detects games Discord shows as "Playing"
- File: `accounts/discord_api.py`

### PSN
- Uses `psnawp` Python library
- QuickSave has a service account — users just enter their PSN username
- Requires user's PSN profile to be set to public
- NPSSO token stored as `PSN_NPSSO_TOKEN` Railway env var
- File: `accounts/psn_api.py`

---

## Session Model (play_sessions/models.py)
Key fields:
- `game` — ForeignKey to Game
- `descriptor` — optional run label (e.g. "Modded", "Speedrun")
- `started_at`, `ended_at`, `duration_seconds`
- `notes` — quick note on session end
- `source` — which platform started the session

### Source Constants
```python
Session.SOURCE_MANUAL = 'manual'
Session.SOURCE_STEAM = 'steam'
Session.SOURCE_XBOX = 'xbox'
Session.SOURCE_DISCORD = 'discord'
Session.SOURCE_PSN = 'psn'
```

**Important:** Each platform only ends sessions it owns. If Steam started a session, Xbox won't touch it. This prevents platform conflicts.

---

## Background Tasks (accounts/tasks.py)
Each platform has:
- `poll_*_for_user(user_id)` — polls one user
- `schedule_*_polling()` — queues async tasks for all eligible users

Shared helpers:
- `_handle_presence(user, game_name, source)` — core logic for start/end sessions
- `_get_or_create_game(user, game_name)` — finds or creates game + fetches RAWG cover art
- `_schedule_all(queryset, task_path)` — generic scheduler

---

## Cron (accounts/cron.py)
Each platform has a `setup_*_polling_schedule()` function that registers a Django-Q schedule.
All schedules run every 5 minutes.

To register schedules against Railway DB locally:
```powershell
$env:DATABASE_URL="postgresql://postgres:<password>@switchback.proxy.rlwy.net:59221/railway"
python manage.py shell
```
Then inside shell:
```python
from accounts.cron import setup_psn_polling_schedule  # or whichever
setup_psn_polling_schedule()
exit()
```
**Never use `railway run` for local shell commands — it overrides DATABASE_URL with the internal URL.**

---

## Key Settings (config/settings.py)
```python
STEAM_API_KEY = env('STEAM_API_KEY')
RAWG_API_KEY = env('RAWG_API_KEY')
DISCORD_CLIENT_ID = env('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = env('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = env('DISCORD_REDIRECT_URI')
MICROSOFT_CLIENT_ID = env('MICROSOFT_CLIENT_ID')
MICROSOFT_CLIENT_SECRET = env('MICROSOFT_CLIENT_SECRET')
MICROSOFT_REDIRECT_URI = env('MICROSOFT_REDIRECT_URI')
PSN_NPSSO_TOKEN = env('PSN_NPSSO_TOKEN')
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')
```

---

## Railway Environment
- **Web service:** runs gunicorn
- **Worker service:** runs Django-Q cluster
- **Postgres service:** Railway managed PostgreSQL
- Both web and worker share the same env vars

---

## Timezone Handling
- All times stored in UTC in the database
- Frontend converts to local time using JavaScript:
```javascript
function convertUTCTimes() {
  document.querySelectorAll('[data-utc]').forEach(function(el) {
    const date = new Date(el.getAttribute('data-utc'));
    el.textContent = date.toLocaleString(undefined, {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: 'numeric', minute: '2-digit', hour12: true
    });
  });
}
document.addEventListener('DOMContentLoaded', convertUTCTimes);
document.addEventListener('htmx:afterSwap', convertUTCTimes);
```
- Use `data-utc="{{ timestamp|date:'c' }}"` on any timestamp element

---

## Frontend Patterns
- **HTMX** for dynamic interactions (hx-boost on most links)
- **hx-boost="false"** required on OAuth redirect links
- **Tailwind CDN** — only core utility classes available (no compiler)
- Brand color: `brand-400/500/600` (green)
- Dark theme throughout: `gray-900` cards, `gray-800` inputs

---

## Completed Features
- [x] User auth (register, login, logout)
- [x] Game library (add, edit, delete games)
- [x] Session tracking (manual start/end with timer)
- [x] Journal entries (per session or standalone)
- [x] Run labels / Descriptors
- [x] Custom fields per game
- [x] Stats (per game + overall)
- [x] Steam auto-tracking
- [x] Xbox auto-tracking (OAuth)
- [x] Discord auto-tracking (OAuth)
- [x] PSN auto-tracking (username-based, service account)
- [x] Sync All / Check Activity button
- [x] PWA support
- [x] Landing page
- [x] RAWG cover art integration
- [x] Pagination on session history
- [x] Session source tracking (no platform conflicts)
- [x] Timezone display fix (UTC → local via JS)

---

## Pinned / Upcoming Features

### Phase 1 — Core Polish (do these next)
- [ ] Game completion status (Playing / Completed / Dropped / Backlog)
- [ ] Game ratings (personal score)
- [ ] Session goals (set a goal before starting)
- [ ] Roblox integration (username-based polling, no OAuth)

### Phase 2 — Retention
- [ ] Gaming Wrapped (yearly recap like Spotify Wrapped)
- [ ] Reminders ("you haven't played X in 2 weeks")
- [ ] Export data (PDF/CSV journal export)
- [ ] Achievement tracking

### Phase 3 — Monetization
- [ ] QuickSave Pro tier ($4-5/month)
  - AI Game Assistant (Claude-powered, uses journal notes + web search)
  - Advanced stats
  - Wrapped feature
- [ ] Embeddable profile card (free marketing)
- [ ] Game recommendations

### Phase 4 — Social
- [ ] Friends system
- [ ] Public profiles
- [ ] Compare stats

### Pinned Ideas (approved, not yet built)
- **AI Game Assistant** — Claude API powered chat on game pages + active session + dedicated page. Uses user's journal notes as context + web search tool for walkthroughs/tips. Needs `ANTHROPIC_API_KEY` in Railway vars.
- **Analytics** — Google Analytics (G-tag) + Plausible for privacy-friendly stats

---

## Monetization Strategy
- Core app free forever
- QuickSave Pro gates: AI assistant, advanced stats, Wrapped, unlimited journal entries
- Embeddable profile cards drive organic growth
- Target price: $4-5/month or $40/year

---

## Known Issues / Notes
- PSN NPSSO token expires periodically — needs manual refresh in Railway env vars
- Xbox XSTS token is 2-step auth: MS access token → user token → XSTS token
- Session showing 0m is expected — background worker updates duration on next poll
- `railway run python manage.py shell` doesn't work locally for DB commands — set DATABASE_URL env var and run `python manage.py shell` directly