from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.logger import get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    logger.info("Starting create_app method")

    app = FastAPI(
        title="Audio Analyzer & Classifier API",
        description="Async audio analysis and classification microservice",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    logger.info("Adding CORS middleware")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check():
        logger.info("Health check endpoint accessed")
        return {"message": "Audio Analyzer API is healthy", "status": "ok"}

    logger.info("FastAPI application creation completed, returning app")
    return app
