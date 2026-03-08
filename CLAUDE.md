# QuickSave — Project Context for Claude Code

## What is QuickSave?
A gaming journal and session tracking web app. Users can track their playtime across platforms, write journal entries after sessions, organize runs/playthroughs, and view stats. Built with the goal of being a full-featured app with eventual monetization.

**Live at:** https://www.quicksave.site
**Repo:** https://github.com/Rilcantus/QuickSave

---

## Studio Context
QuickSave is the first live product under **Disrat Studios LLC** (Oregon, USA — filing in progress). All development, monetization, and legal decisions are made under the studio umbrella.

**Studio principles:**
- Legal first — Privacy Policy, ToS, and DMCA before any public marketing push
- Protect before you promote — app stays in friend-testing mode until LLC is filed and Phase 2 hardening is complete
- User interaction before monetization — build something people love, then charge for it
- Every project follows the 4-phase framework: Legal → Technical Hardening → Monetization → Launch

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

## Current Status — Friend Testing Only
QuickSave is currently in private testing with a small group of friends. **No public marketing until:**
- Disrat Studios LLC is filed and active
- Phase 2 hardening is complete
- Privacy Policy + ToS are published on the site

This is intentional — protect before you promote.

---

## Phase 2 — Technical Hardening (current priority)
These must be done before any public launch. Work through them in order.

### Security
- [ ] Rate limiting on login + register endpoints — install `django-axes`
- [ ] Account lockout after failed login attempts — also handled by `django-axes`
- [ ] Email verification on signup — prevent throwaway/fake accounts
- [ ] Confirm `DEBUG=False` reads from `.env` and is never hardcoded
- [ ] Confirm no stack traces exposed on 404/500 in production
- [ ] CSRF audit — search all templates for `<form>` tags missing `{% csrf_token %}`
- [ ] Input sanitization / XSS review on journal entry fields
- [ ] Password strength validators in `AUTH_PASSWORD_VALIDATORS` in settings
- [ ] HTTPS enforced, HSTS header set (check Railway config)

### User Data & Compliance
- [ ] Data export — view that dumps all user data (games, sessions, journal entries) as JSON/CSV
- [ ] Delete account — view that wipes all user data and the account itself
- [ ] Privacy Policy page — generate at Termly.io, add to `templates/legal/privacy.html`
- [ ] Terms of Service page — generate at Termly.io, add to `templates/legal/terms.html`
- [ ] DMCA Policy page — boilerplate, add to `templates/legal/dmca.html`
- [ ] Link all legal pages in site footer
- [ ] Steam OAuth scope audit — confirm only minimum required data is requested

### Polish
- [ ] Custom 404 page — `templates/404.html`
- [ ] Custom 500 page — `templates/500.html`
- [ ] Empty state screens — new user with no games should see a helpful prompt, not blank content
- [ ] Onboarding flow — after register, guide user to add first game + connect a platform
- [ ] Loading states / skeleton screens on HTMX requests
- [ ] Better error messages on failed platform connections

### Installing django-axes (rate limiting)
```bash
pip install django-axes
```
Add to `INSTALLED_APPS`:
```python
'axes',
```
Add to `MIDDLEWARE` (must be last):
```python
'axes.middleware.AxesMiddleware',
```
Add to `AUTHENTICATION_BACKENDS`:
```python
'axes.backends.AxesStandaloneBackend',
```
Add config to settings:
```python
AXES_FAILURE_LIMIT = 5          # lock after 5 failed attempts
AXES_COOLOFF_TIME = 1           # unlock after 1 hour
AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'
AXES_RESET_ON_SUCCESS = True
```
Run migrations: `python manage.py migrate`

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
- [ ] QuickSave Pro tier ($4.99/month or $40/year)
  - AI Game Assistant (Claude-powered, uses journal notes + web search)
  - Advanced stats
  - Wrapped feature
  - Unlimited journal entries
- [ ] Lifetime deal — $49 one-time, available 30 days at launch only
- [ ] Embeddable profile card (free marketing)
- [ ] Game recommendations
- [ ] Stripe integration via `dj-stripe`
  - Two products: Pro Monthly + Lifetime
  - Webhook handler: `checkout.session.completed` → activate Pro on user
  - `/upgrade/` view → Stripe Checkout redirect
  - `/billing/` view → manage plan, update card, cancel

### Phase 4 — Social
- [ ] Friends system
- [ ] Public profiles
- [ ] Compare stats

### Pinned Ideas (approved, not yet built)
- **AI Game Assistant** — Claude API powered chat on game pages + active session + dedicated page. Uses user's journal notes as context + web search tool for walkthroughs/tips. Needs `ANTHROPIC_API_KEY` in Railway vars. Pro tier only.
- **Analytics** — Google Analytics (G-tag) + Plausible for privacy-friendly stats
- **Desktop Companion App** — lightweight system tray app for richer auto-tracking including Discord RPC. Planned as Coming Soon on landing page.
- **Xbox / PlayStation via companion** — cross-platform tracking beyond Steam via desktop app.
- **Mobile App** — native iOS and Android, longer term.

---

## Monetization Strategy
- Core app free forever
- QuickSave Pro gates: AI assistant, advanced stats, Wrapped, unlimited journal entries
- Embeddable profile cards drive organic growth
- Target price: $4.99/month or $40/year
- Lifetime deal: $49 at launch (30 days only) — drives early cash and rewards early adopters
- Revenue target: 200 Pro users = ~$1,000/mo. Realistic within 6 months of proper public launch.

---

## Legal Checklist (Disrat Studios LLC)
Do not publicly launch or accept payments until these are complete.

- [ ] File Disrat Studios LLC — filinginoregon.com — $100, ~20 min
- [ ] Get EIN — irs.gov → Apply for EIN Online — free, instant
- [ ] Open business bank account — local credit union, bring LLC approval + EIN
- [ ] Set up Stripe under LLC — stripe.com
- [ ] Transfer quicksave.site domain ownership to Disrat Studios LLC
- [ ] Publish Privacy Policy — Termly.io, link in footer
- [ ] Publish Terms of Service — Termly.io, link in footer
- [ ] Publish DMCA Policy — boilerplate template, link in footer
- [ ] Annual report reminder set — $100/yr due on LLC anniversary date

---

## Launch Sequence (when LLC + Phase 2 are done)
1. Soft launch — share with a slightly wider group of testers, fix top issues
2. Stripe integration live — test full payment flow in Stripe test mode
3. Free vs Pro feature gates implemented and tested
4. Transactional emails set up — welcome, receipt, cancellation
5. Lifetime Deal page live — $49, 30 days only
6. Public launch posts:
   - r/patientgamers, r/gaming, r/gamedev
   - Relevant Discord gaming communities
   - Product Hunt — schedule for a Tuesday
   - X/Twitter build-in-public thread

---

## Disrat Studios — Other Projects
QuickSave is the active project. These are queued for after QuickSave reaches monetization:

| Project | Description | Stack | Monetization |
|---|---|---|---|
| AdSpark | Local ad generator for small businesses | HTML/JS + FastAPI | Free → $9–29/mo |
| BrandChecker | Name availability scanner (domains, social, dev) | HTML/JS + FastAPI | Free + domain affiliates |
| FightIQ | Combat sports head-to-head predictor | HTML/JS + FastAPI | Free → Pro data tier |
| CreatorForge | AI micro-app suite for writers/GMs | HTML/JS + FastAPI | $9/mo bundle |
| Worldie | World-building editor for authors + RPG designers | Django, HTMX, Tailwind | $8–12/mo Pro |
| Spaci | Social world-building platform (after Worldie) | Django, HTMX, Tailwind | Creator marketplace |
| Tower Defense | Hybrid shooter + tower defense zombie game | Godot (GDScript) | Steam $9.99–19.99 |

All projects follow the same 4-phase framework: Legal → Technical Hardening → Monetization → Launch.
All projects ship under Disrat Studios LLC.

---

## Known Issues / Notes
- PSN NPSSO token expires periodically — needs manual refresh in Railway env vars
- Xbox XSTS token is 2-step auth: MS access token → user token → XSTS token
- Session showing 0m is expected — background worker updates duration on next poll
- `railway run python manage.py shell` doesn't work locally for DB commands — set DATABASE_URL env var and run `python manage.py shell` directly