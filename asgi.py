import uvicorn

from app.config.base import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=settings.FASTAPI_RELOAD,
        log_level="info",
        reload_excludes=["*.log", "logs/*", "app/logs/*"],
    )
