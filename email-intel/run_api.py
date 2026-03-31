from api.main import app


if __name__ == "__main__":
    import os

    from alembic import command
    from alembic.config import Config
    import uvicorn

    has_single_token = bool(os.getenv("API_AUTH_TOKEN"))
    has_rotation_tokens = bool(os.getenv("API_AUTH_TOKENS"))
    if not has_single_token and not has_rotation_tokens:
        raise RuntimeError("API_AUTH_TOKEN or API_AUTH_TOKENS is required")
    if not os.getenv("APP_ENCRYPTION_KEY"):
        raise RuntimeError("APP_ENCRYPTION_KEY is required")

    command.upgrade(Config("alembic.ini"), "head")
    uvicorn.run(app, host="0.0.0.0", port=8000)
