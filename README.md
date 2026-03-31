# bruv-mail

An ADHD compatible mailbox system.

## Current Status

The repository now includes a working Phase 1 + Phase 2 baseline for `email-intel`:

- FastAPI app bootstrapped with DB initialization.
- SQLAlchemy models and session management.
- IMAP ingestion worker with incremental UID sync.
- Duplicate message protection per account.
- Basic rule-based email tagging.
- Basic task extraction from email content.
- Message filtering and pagination in the API.
- Alembic migrations for schema versioning.
- Encrypted credential storage for IMAP passwords.

## Quick Start

1. Create and activate a virtual environment (already present in this repo if using `venv/`).
2. Install dependencies:

```bash
pip install -r email-intel/requirements.txt
```

3. Start the API:

```bash
cd email-intel
python run_api.py
```

4. In another shell, start the IMAP worker:

```bash
cd email-intel
python run_worker.py
```

By default the app uses SQLite at `email-intel/email_intel.db`.

Set `DATABASE_URL` to override, for example:

```bash
export DATABASE_URL="sqlite:///./email_intel.db"
```

Set required app secrets before running API/worker:

```bash
export APP_ENCRYPTION_KEY="replace-with-fernet-key"
export API_AUTH_TOKEN="replace-with-api-token"
export API_ADMIN_TOKEN="replace-with-admin-token"
```

For token rotation, you can provide multiple valid tokens:

```bash
export API_AUTH_TOKENS="token-old,token-new"
```

Optional dedicated admin token set:

```bash
export API_ADMIN_TOKENS="admin-token-current,admin-token-next"
```

Generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set `APP_ENCRYPTION_KEY` to control credential encryption (must be a urlsafe base64 Fernet key):

```bash
export APP_ENCRYPTION_KEY="replace-with-your-fernet-key"
```

Generate a valid key:

```bash
/home/benr/repos/bruv-mail/venv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Migrations

Run migrations manually:

```bash
cd email-intel
/home/benr/repos/bruv-mail/venv/bin/python -m alembic upgrade head
```

`run_api.py` and `run_worker.py` automatically run `alembic upgrade head` before starting.

## API Endpoints

- `GET /health`
- `POST /accounts`
- `GET /accounts`
- `PATCH /accounts/{id}` with body `{"display_name":"Inbox","is_active":true}`
- `GET /messages?tag=<tag>&account_id=<id>&from_addr=<text>&date_from=<iso>&date_to=<iso>&limit=50&offset=0`
- `GET /messages/{id}`
- `GET /tags`
- `GET /tasks?status=open|done|dismissed&due_before=<iso>&due_after=<iso>&limit=50&offset=0`
- `PATCH /tasks/{id}` with body `{"status":"open|done|dismissed"}`

All endpoints except `GET /health` require header:

- `X-API-Key: <API_AUTH_TOKEN>`

If `API_AUTH_TOKENS` is set, any listed token in the comma-separated value is accepted.

If `API_ADMIN_TOKEN` / `API_ADMIN_TOKENS` is unset, admin endpoints fall back to API auth tokens.

Admin token management endpoints:

- `GET /auth/tokens`
- `POST /auth/tokens` with body `{"token":"optional-explicit-token","ttl_minutes":60,"expires_at":"optional-iso","note":"optional"}`
- `POST /auth/tokens/revoke` with body `{"token":"runtime-token-to-revoke"}`

`POST /auth/tokens` returns the raw token exactly once in response so clients can store it safely.

## Task Extraction Rules (Current MVP)

When a new email is ingested, a task is created if subject/body contains one of:

- `todo`
- `to do`
- `action required`
- `please`
- `remind me`

Due dates are inferred from:

- `today`
- `tomorrow`
- `by YYYY-MM-DD`

## Docker Compose (API + Worker + Postgres)

Start the stack:

```bash
docker compose -f email-intel/docker-compose.yml up --build
```

Then use the API at `http://localhost:8000`.

## Tests

Run integration tests:

```bash
cd email-intel
/home/benr/repos/bruv-mail/venv/bin/python -m pytest -q
```
