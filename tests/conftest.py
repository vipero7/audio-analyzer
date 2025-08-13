import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.api.dependencies import get_audio_analyzer_service, get_metrics_service
from app.main import create_app
from app.services.analyzer import AudioAnalyzerService
from app.services.redis import RedisService


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis_service():
    mock_redis = AsyncMock(spec=RedisService)
    mock_redis.connect = AsyncMock()
    mock_redis.close = AsyncMock()
    mock_redis.is_connected.return_value = True
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.redis = AsyncMock()
    mock_redis.redis.scan.return_value = (0, [])
    mock_redis.redis.delete.return_value = 0
    return mock_redis


@pytest.fixture
def mock_audio_analyzer_service():
    mock_analyzer = AsyncMock(spec=AudioAnalyzerService)
    mock_analyzer.analyze_audio.return_value = {
        "duration": 5.23,
        "sample_rate": 44100,
        "channels": 2,
        "bit_depth": 16,
        "file_size": 461814,
        "format": "wav",
        "classification": "music",
        "confidence": 0.89,
    }
    return mock_analyzer


@pytest.fixture
def mock_metrics_service():
    mock_metrics = MagicMock()
    mock_metrics.record_request = MagicMock()
    mock_metrics.record_error = MagicMock()

    mock_timer = MagicMock()
    mock_timer.__enter__ = MagicMock(return_value=mock_timer)
    mock_timer.__exit__ = MagicMock(return_value=None)
    mock_metrics.processing_duration.time.return_value = mock_timer

    return mock_metrics


@pytest.fixture
def test_app(mock_redis_service, mock_audio_analyzer_service, mock_metrics_service):
    app = create_app()

    app.dependency_overrides[get_audio_analyzer_service] = lambda: mock_audio_analyzer_service
    app.dependency_overrides[get_metrics_service] = lambda: mock_metrics_service

    app.state.redis_service = mock_redis_service
    app.state.audio_analyzer_service = mock_audio_analyzer_service
    app.state.metrics_service = mock_metrics_service

    yield app

    app.dependency_overrides.clear()


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


@pytest_asyncio.fixture
async def async_client(test_app):
    async with AsyncClient(base_url="http://test") as ac:
        ac.app = test_app
        yield ac


@pytest.fixture
def sample_audio_data():
    return {
        "duration": 5.23,
        "sample_rate": 44100,
        "channels": 2,
        "bit_depth": 16,
        "file_size": 461814,
        "format": "wav",
        "classification": "music",
        "confidence": 0.89,
    }


@pytest.fixture
def valid_audio_urls():
    return [
        "https://example.com/test.mp3",
        "https://example.com/test.wav",
        "https://example.com/test.ogg",
        "https://example.com/test.m4a",
        "https://example.com/test.flac",
    ]


@pytest.fixture
def invalid_audio_urls():
    return [
        "https://example.com/test.txt",
        "https://example.com/test.pdf",
        "not-a-url",
        "",
        "ftp://example.com/test.wav",
    ]
