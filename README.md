# Utilization Dashboard

FastAPI dashboard that pulls login activity from Supabase and surfaces utilization metrics (active days, today's logins, last login trends) on a simple HTML page.

## Prerequisites

- Python 3.11+
- Supabase project with a `login_events` table:
  ```sql
  create table if not exists public.login_events (
    id bigint generated always as identity primary key,
    username text not null,
    login_timestamp timestamptz not null default now()
  );
  ```
- Update the exclusion list in `app/routers/metrics.py` (`EXCLUDED_USERS`) if you want to omit certain usernames from calculations.

## Local setup

```bash
python -m venv .venv
.\.venv\Scripts\activate          # Windows
source .venv/bin/activate         # macOS/Linux
pip install -r requirements.txt
```

Create a `.env` (see `.env.example`) with:

```
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Run the dashboard

```bash
uvicorn app.main:app --reload
```

- Dashboard UI: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs (see `/api/metrics/login-summary`)

## Supabase policies

- Enable Row Level Security on `login_events`.
- Add select policies allowing the anon key (if needed) and the service role to read from `login_events`.

## Deployment notes

- Provide the same environment variables via your hosting platform (Render, Fly.io, etc.).
- Keep the service role key secret; only expose the anon key to public clients if necessary.
