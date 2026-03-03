# 🎮 QuickSave

A private, reflection-first journaling app for gamers. Log sessions, track progress, and capture notes across all your games — without the social noise.

---

## Tech Stack

- **Backend:** Django
- **Frontend:** HTMX + Tailwind CSS
- **Database:** PostgreSQL
- **Auth:** Django built-in auth

---

## Project Structure

```
quicksave/
├── config/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/               # User auth & profiles
├── games/                  # Game, Descriptor, CustomField models
├── play_sessions/          # Session tracking
├── journal/                # Journal entries
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
├── .env                    # Environment variables (never commit)
├── requirements.txt
└── manage.py
```

---

## Local Setup

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd quicksave
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
# Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install django psycopg2-binary django-environ pillow
pip freeze > requirements.txt
```

### 4. Start the Django project

```bash
django-admin startproject config .
```

### 5. Create the apps

```bash
python manage.py startapp accounts
python manage.py startapp games
python manage.py startapp play_sessions
python manage.py startapp journal
```

### 6. Set up environment variables

Create a `.env` file in the project root:

```
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://youruser:yourpassword@localhost:5432/quicksave
```

> ⚠️ Never commit `.env` to version control.

### 7. Create the PostgreSQL database

```bash
createdb quicksave
```

### 8. Run migrations

```bash
python manage.py migrate
```

### 9. Create a superuser

```bash
python manage.py createsuperuser
```

### 10. Start the dev server

```bash
python manage.py runserver
```

Visit [http://localhost:8000](http://localhost:8000)

---

## Data Models

| Model | Description |
|---|---|
| `User` | Django built-in auth |
| `Game` | A game the user plays |
| `Descriptor` | Optional run label (e.g. "Modded Run", "STR Build") |
| `CustomFieldDefinition` | User-defined metadata fields per game |
| `CustomFieldChoice` | Reusable dropdown options for choice-type fields |
| `Session` | A single play period with start/end time |
| `CustomFieldValue` | Per-session values for custom fields |
| `JournalEntry` | Reflection tied to a session or standalone |

---

## MVP Features

- [x] Data model design
- [ ] Project scaffolding
- [ ] User auth (register, login, logout)
- [ ] Game CRUD
- [ ] Descriptor management
- [ ] Custom field definitions
- [ ] Session start/end flow
- [ ] Custom field auto-fill from last session
- [ ] Journal entry on session end
- [ ] Standalone journal entries

## Deferred Features

- Auto session detection
- Platform integrations (Steam, consoles)
- Media attachments
- Analytics
- Social features
- PWA / mobile app

---

## Contributing

This is a personal project in active development. No contributions accepted at this time.

---

## License

MIT