from imap_worker.worker import run_worker


if __name__ == "__main__":
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config("alembic.ini"), "head")
    run_worker()
