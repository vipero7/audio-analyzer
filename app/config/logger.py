import sys

from loguru import logger

from app.config.base import Config


def setup_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        level="INFO",
    )

    if Config.ENV == "local":
        Config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file_path = Config.LOG_DIR / "app.log"

        logger.add(
            log_file_path,
            rotation="00:00",
            retention="10 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
            level="DEBUG",
        )


def get_logger(name: str):
    return logger.bind(component=name)
