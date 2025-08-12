from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Config:
    ENV = config("ENV", default="local")
    FASTAPI_HOST = config("FASTAPI_HOST", default="0.0.0.0")
    FASTAPI_PORT = config("FASTAPI_PORT", default=8000, cast=int)
    FASTAPI_RELOAD = config("FASTAPI_RELOAD", default=True, cast=bool)
    BASE_DIR = BASE_DIR
    APP_DIR = BASE_DIR / "app"
    LOG_DIR = APP_DIR / "logs"
