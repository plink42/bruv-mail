from imap_worker.worker import run_worker


if __name__ == "__main__":
    import os

    from alembic import command
    from alembic.config import Config

    if not os.getenv("APP_ENCRYPTION_KEY"):
        raise RuntimeError("APP_ENCRYPTION_KEY is required")

    command.upgrade(Config("alembic.ini"), "head")
    run_worker()
