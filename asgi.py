import uvicorn

from app.config.base import Config

if __name__ == "__main__":
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=Config.FASTAPI_HOST,
        port=Config.FASTAPI_PORT,
        reload=Config.FASTAPI_RELOAD,
        log_level="info",
        reload_excludes=["*.log", "logs/*", "app/logs/*"],
    )
