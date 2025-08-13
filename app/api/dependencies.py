from fastapi import Request

from app.services.analyzer import AudioAnalyzerService
from app.services.metrics import MetricsService
from app.services.redis import RedisService


def get_redis_service(request: Request) -> RedisService:
    return request.app.state.redis_service


def get_audio_analyzer_service(request: Request) -> AudioAnalyzerService:
    return request.app.state.audio_analyzer_service


def get_metrics_service(request: Request) -> MetricsService:
    return request.app.state.metrics_service
