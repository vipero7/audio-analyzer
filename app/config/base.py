from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    ENV: str
    FASTAPI_HOST: str
    FASTAPI_PORT: int
    FASTAPI_RELOAD: bool

    REDIS_URL: str
    CACHE_TTL: int
    DOWNLOAD_TIMEOUT: int
    MAX_FILE_SIZE: int
    MAX_DURATION: float
    TEMP_DIR: str

    BASE_DIR: Path = BASE_DIR
    APP_DIR: Path = BASE_DIR / "app"
    LOG_DIR: Path = BASE_DIR / "app" / "logs"

    model_config = {"env_file": str(ENV_PATH), "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
