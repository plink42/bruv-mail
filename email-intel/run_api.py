from api.main import app


if __name__ == "__main__":
    from alembic import command
    from alembic.config import Config
    import uvicorn

    command.upgrade(Config("alembic.ini"), "head")
    uvicorn.run(app, host="0.0.0.0", port=8000)
