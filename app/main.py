from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.router import api_router
from app.config.logger import get_logger, setup_logging
from app.services.analyzer import AudioAnalyzerService
from app.services.metrics import MetricsService
from app.services.redis import RedisService

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting audio analyzer application")

    redis_service = RedisService()
    try:
        await redis_service.connect()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        logger.warning("Running without Redis cache")

    app.state.redis_service = redis_service
    app.state.audio_analyzer_service = AudioAnalyzerService(redis_service)
    app.state.metrics_service = MetricsService()

    logger.info("Application startup completed")
    yield

    logger.info("Shutting down application")
    await redis_service.close()


def create_app() -> FastAPI:
    logger.info("Starting create_app method")

    app = FastAPI(
        title="Audio Analyzer & Classifier API",
        description="Async audio analysis and classification microservice",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    logger.info("Adding CORS middleware")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("Setting up Prometheus metrics")
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app)

    logger.info("Including v1 api routers")
    app.include_router(api_router, prefix="/v1", tags=["audio"])

    @app.get("/health")
    async def health_check():
        logger.info("Health check endpoint accessed")
        return {"message": "Audio Analyzer API is healthy", "status": "ok"}

    logger.info("FastAPI application creation completed, returning app")
    return app
