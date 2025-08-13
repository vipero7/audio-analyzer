from unittest.mock import AsyncMock

import pytest

from app.repository.cache import CacheRepository
from app.services.redis import RedisService


class TestCacheRepository:

    @pytest.fixture
    def mock_redis_service(self):
        mock_redis = AsyncMock(spec=RedisService)
        mock_redis.is_connected.return_value = True
        return mock_redis

    @pytest.fixture
    def cache_repository(self, mock_redis_service):
        return CacheRepository(mock_redis_service)

    def test_generate_key(self, cache_repository):
        url1 = "https://example.com/test.wav"
        url2 = "https://example.com/test.mp3"

        key1 = cache_repository.generate_key(url1)
        key2 = cache_repository.generate_key(url2)

        assert key1 != key2
        assert key1 == cache_repository.generate_key(url1)
        assert key1.startswith("audio:")
        assert len(key1) == len("audio:") + 16

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache_repository, mock_redis_service):
        test_data = {"duration": 5.0, "classification": "music"}
        mock_redis_service.get.return_value = '{"duration": 5.0, "classification": "music"}'

        result = await cache_repository.get("https://example.com/test.wav")

        assert result == test_data
        mock_redis_service.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_repository, mock_redis_service):
        mock_redis_service.get.return_value = None

        result = await cache_repository.get("https://example.com/test.wav")

        assert result is None
        mock_redis_service.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_redis_disconnected(self, cache_repository, mock_redis_service):
        mock_redis_service.is_connected.return_value = False

        result = await cache_repository.get("https://example.com/test.wav")

        assert result is None
        mock_redis_service.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_success(self, cache_repository, mock_redis_service):
        test_data = {"duration": 5.0, "classification": "music"}
        mock_redis_service.setex.return_value = True

        result = await cache_repository.set("https://example.com/test.wav", test_data, 3600)

        assert result is True
        mock_redis_service.setex.assert_called_once()

        call_args = mock_redis_service.setex.call_args
        assert call_args[0][1] == 3600
        assert "audio:" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_set_redis_disconnected(self, cache_repository, mock_redis_service):
        mock_redis_service.is_connected.return_value = False
        test_data = {"duration": 5.0, "classification": "music"}

        result = await cache_repository.set("https://example.com/test.wav", test_data)

        assert result is False
        mock_redis_service.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_redis_error(self, cache_repository, mock_redis_service):
        mock_redis_service.setex.side_effect = Exception("Redis error")
        test_data = {"duration": 5.0, "classification": "music"}

        try:
            await cache_repository.set("https://example.com/test.wav", test_data)
        except Exception:
            pass

        mock_redis_service.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_workflow(self, cache_repository, mock_redis_service):
        url = "https://example.com/test.wav"
        test_data = {"duration": 5.0, "classification": "music"}

        mock_redis_service.get.return_value = None
        result = await cache_repository.get(url)
        assert result is None

        mock_redis_service.setex.return_value = True
        set_result = await cache_repository.set(url, test_data, 3600)
        assert set_result is True

        mock_redis_service.get.return_value = '{"duration": 5.0, "classification": "music"}'
        cached_result = await cache_repository.get(url)
        assert cached_result == test_data
