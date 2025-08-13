import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoints:

    async def test_main_health_endpoint(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "Audio Analyzer API" in data["message"]

    async def test_redis_health_check_healthy(self, client: AsyncClient):
        response = await client.get("/v1/redis/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_cache_test_endpoint(self, client: AsyncClient):
        response = await client.get("/v1/cache/test")
        assert response.status_code == 200
        data = response.json()
        assert data["working"] is True


@pytest.mark.asyncio
class TestAudioAnalysisEndpoints:

    async def test_analyze_audio_success(self, client: AsyncClient):
        response = await client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/test.wav"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["classification"] == "music"
        assert data["data"]["duration"] == 5.23
        assert data["data"]["sample_rate"] == 44100

    async def test_analyze_audio_with_different_formats(
        self, client: AsyncClient, valid_audio_urls
    ):
        for url in valid_audio_urls:
            response = await client.post("/v1/audio/analyze", json={"audio_url": url})
            assert response.status_code == 200
            assert response.json()["status"] == "success"

    async def test_analyze_audio_invalid_format(self, client: AsyncClient):
        response = await client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/test.txt"}
        )
        assert response.status_code == 422

    async def test_analyze_audio_malformed_url(self, client: AsyncClient):
        response = await client.post("/v1/audio/analyze", json={"audio_url": "not-a-url"})
        assert response.status_code == 422

    async def test_analyze_audio_missing_url(self, client: AsyncClient):
        response = await client.post("/v1/audio/analyze", json={})
        assert response.status_code == 422

    async def test_analyze_audio_file_not_found(
        self, client: AsyncClient, mock_audio_analyzer_service
    ):
        mock_audio_analyzer_service.analyze_audio.side_effect = FileNotFoundError("File not found")

        response = await client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/nonexistent.wav"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_analyze_audio_validation_error(
        self, client: AsyncClient, mock_audio_analyzer_service
    ):
        mock_audio_analyzer_service.analyze_audio.side_effect = ValueError("Invalid audio file")

        response = await client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/invalid.wav"}
        )
        assert response.status_code == 400
        assert "Invalid audio file" in response.json()["detail"]

    async def test_analyze_audio_internal_error(
        self, client: AsyncClient, mock_audio_analyzer_service
    ):
        mock_audio_analyzer_service.analyze_audio.side_effect = Exception("Unexpected error")

        response = await client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/test.wav"}
        )
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


@pytest.mark.asyncio
class TestCacheEndpoints:

    async def test_clear_cache_success(self, client: AsyncClient):
        response = await client.delete("/v1/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data
        assert isinstance(data["deleted_count"], int)

    async def test_clear_cache_redis_disconnected(self, client: AsyncClient, mock_redis_service):
        mock_redis_service.is_connected.return_value = False

        response = await client.delete("/v1/cache/clear")
        assert response.status_code == 503
        assert "Redis not connected" in response.json()["detail"]


@pytest.mark.asyncio
class TestMetricsEndpoints:

    async def test_metrics_test_endpoint(self, client: AsyncClient):
        response = await client.get("/v1/metrics/test")
        assert response.status_code == 200
        data = response.json()
        assert "Metrics recorded" in data["message"]
        assert "http://localhost:8001/metrics" in data["check"]

    async def test_prometheus_metrics_endpoint(self, client: AsyncClient):
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


@pytest.mark.asyncio
class TestAPIDocumentation:

    async def test_openapi_docs(self, client: AsyncClient):
        response = await client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    async def test_redoc_docs(self, client: AsyncClient):
        response = await client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    async def test_openapi_schema(self, client: AsyncClient):
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "/v1/audio/analyze" in schema["paths"]
