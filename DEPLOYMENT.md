# bruv-mail Deployment Guide

This guide covers reliable deployment for the current stack:

- Backend API (FastAPI)
- IMAP worker
- PostgreSQL
- React frontend (Vite, static build)

## 1. Deployment Modes

Choose one:

1. Local process mode: run API and worker directly from Python virtualenv, optional local Postgres.
2. Docker backend mode: run only backend services with [email-intel/docker-compose.yml](email-intel/docker-compose.yml).
3. Full Docker mode: run frontend + backend with root [docker-compose.yml](docker-compose.yml).

## 2. Prerequisites

- Docker + Docker Compose plugin (recommended for deployment)
- Or Python 3.12+ and Node 18+ for non-Docker setup
- Open ports:
  - 3000 (frontend)
  - 8000 (API)
  - 5432 (Postgres, optional to expose externally)

## 3. Required Environment Variables

Set these in your shell or in a `.env` file (for Docker Compose):

- `APP_ENCRYPTION_KEY`: Fernet key used to encrypt IMAP passwords at rest
- `API_AUTH_TOKEN`: primary API token for user/API access
- `API_ADMIN_TOKEN`: admin token for auth token management endpoints

Optional token rotation variables:

- `API_AUTH_TOKENS`: comma-separated additional valid API tokens
- `API_ADMIN_TOKENS`: comma-separated additional valid admin tokens

Generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Example `.env`:

```dotenv
APP_ENCRYPTION_KEY=replace-with-generated-fernet-key
API_AUTH_TOKEN=replace-with-strong-api-token
API_ADMIN_TOKEN=replace-with-strong-admin-token
```

## 4. Option A: Full Stack with Docker (Recommended)

### 4.1 Configure environment

At repository root:

```bash
cp .env.example .env
```

Edit `.env` and set secure values.

### 4.2 Start services

```bash
docker compose up --build -d
```

Services started from [docker-compose.yml](docker-compose.yml):

- `db` (Postgres)
- `api` (FastAPI, runs Alembic migrations on startup)
- `worker` (IMAP polling worker, runs migrations on startup)
- `frontend` (static React build)

### 4.3 Verify health

```bash
curl -s http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### 4.4 Verify authenticated endpoint

```bash
curl -s -H "X-API-Key: $API_AUTH_TOKEN" http://localhost:8000/accounts
```

## 5. Option B: Backend Only with Docker

If you want only API + worker + Postgres (no frontend):

```bash
docker compose -f email-intel/docker-compose.yml up --build -d
```

Use API at `http://localhost:8000`.

## 6. Option C: Local Process Deployment

### 6.1 Backend

```bash
cd email-intel
/home/benr/repos/bruv-mail/venv/bin/pip install -r requirements.txt
export APP_ENCRYPTION_KEY="<fernet-key>"
export API_AUTH_TOKEN="<api-token>"
export API_ADMIN_TOKEN="<admin-token>"
```

Start API:

```bash
/home/benr/repos/bruv-mail/venv/bin/python run_api.py
```

Start worker in another shell:

```bash
cd email-intel
/home/benr/repos/bruv-mail/venv/bin/python run_worker.py
```

### 6.2 Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run build
npm run preview
```

For local dev server:

```bash
npm run dev
```

## 7. Migrations and Schema Management

Alembic config is under [email-intel/alembic.ini](email-intel/alembic.ini) and [email-intel/alembic/env.py](email-intel/alembic/env.py).

Manual migration commands:

```bash
cd email-intel
/home/benr/repos/bruv-mail/venv/bin/python -m alembic current
/home/benr/repos/bruv-mail/venv/bin/python -m alembic upgrade head
/home/benr/repos/bruv-mail/venv/bin/python -m alembic history
```

Notes:

- `run_api.py` and `run_worker.py` already run `alembic upgrade head` at startup.
- Keep schema changes migration-driven; do not rely on `Base.metadata.create_all()` in production.

## 8. Frontend Deployment Notes

- Frontend API base URL is read from `VITE_API_URL` in [frontend/src/api/client.ts](frontend/src/api/client.ts).
- For Vite builds, `VITE_*` values are injected at build time, not runtime.
- If your API host differs from `http://localhost:8000`, set `VITE_API_URL` before building frontend artifacts.

Example:

```bash
cd frontend
VITE_API_URL="https://api.example.com" npm run build
```

## 9. Security Baseline

- Use strong random tokens for API and admin access.
- Do not commit `.env` with real secrets.
- Restrict Postgres port exposure if external DB access is not required.
- Use TLS termination via reverse proxy (nginx/caddy/traefik) in production.
- Rotate API tokens periodically using admin endpoints:
  - `GET /auth/tokens`
  - `POST /auth/tokens`
  - `POST /auth/tokens/revoke`

## 10. Backup and Restore (Postgres)

From repo root, backup database in running Docker stack:

```bash
docker compose exec -T db pg_dump -U email_intel email_intel > backup.sql
```

Restore:

```bash
cat backup.sql | docker compose exec -T db psql -U email_intel -d email_intel
```

## 11. Upgrade Procedure

For deployments using root `docker compose`:

1. Pull latest code.
2. Update `.env` only if needed.
3. Rebuild and restart:

```bash
docker compose up --build -d
```

4. Verify:

```bash
curl -s http://localhost:8000/health
```

## 12. Troubleshooting

### API fails at startup with encryption key errors

- Ensure `APP_ENCRYPTION_KEY` is set and is a valid Fernet key.

### 401/403 from API requests

- Ensure `X-API-Key` header matches a configured token.
- Confirm token rotation values in `API_AUTH_TOKENS` or admin-created token state.

### Frontend cannot reach API

- Confirm API is reachable at expected URL from browser.
- Rebuild frontend if `VITE_API_URL` changed.

### Worker not ingesting mail

- Confirm accounts are active.
- Check worker logs:

```bash
docker compose logs -f worker
```

### Inspect service logs

```bash
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f frontend
docker compose logs -f db
```
