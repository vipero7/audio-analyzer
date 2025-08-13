import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestIntegration:

    async def test_full_audio_analysis_workflow(
        self, client: AsyncClient, mock_audio_analyzer_service
    ):
        """Test complete workflow from API request to response"""

        mock_audio_analyzer_service.analyze_audio.return_value = {
            "duration": 60.0,
            "sample_rate": 44100,
            "channels": 2,
            "bit_depth": 16,
            "file_size": 2500000,
            "format": "wav",
            "classification": "music",
            "confidence": 0.92,
        }

        response = await client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/test.wav"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["data"]["duration"] == 60.0
        assert data["data"]["sample_rate"] == 44100
        assert data["data"]["channels"] == 2
        assert data["data"]["classification"] == "music"
        assert data["data"]["confidence"] == 0.92

        mock_audio_analyzer_service.analyze_audio.assert_called_once_with(
            "https://example.com/test.wav"
        )

    async def test_error_handling_workflow(self, client: AsyncClient, mock_audio_analyzer_service):
        """Test error handling through the entire stack"""

        mock_audio_analyzer_service.analyze_audio.side_effect = ValueError("File too large")

        response = await client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/huge-file.wav"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "File too large" in data["detail"]

    async def test_metrics_collection_workflow(self, client: AsyncClient, mock_metrics_service):
        """Test that metrics are collected during API calls"""

        await client.post("/v1/audio/analyze", json={"audio_url": "https://example.com/test.wav"})

        mock_metrics_service.record_request.assert_called()
        mock_metrics_service.processing_duration.time.assert_called()

    async def test_cache_integration_workflow(self, client: AsyncClient, mock_redis_service):
        """Test cache integration in the workflow"""

        response = await client.get("/v1/redis/health")
        assert response.status_code == 200

        response = await client.get("/v1/cache/test")
        assert response.status_code == 200

        response = await client.delete("/v1/cache/clear")
        assert response.status_code == 200

    async def test_validation_workflow(self, client: AsyncClient):
        """Test request validation workflow"""

        invalid_requests = [
            {},
            {"audio_url": "not-a-url"},
            {"audio_url": "https://example.com/file.txt"},
            {"audio_url": "ftp://example.com/test.wav"},
        ]

        for invalid_request in invalid_requests:
            response = await client.post("/v1/audio/analyze", json=invalid_request)
            assert response.status_code == 422

    async def test_health_check_workflow(self, client: AsyncClient):
        """Test health check endpoints workflow"""

        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        response = await client.get("/v1/redis/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        response = await client.get("/v1/metrics/test")
        assert response.status_code == 200

    async def test_api_documentation_workflow(self, client: AsyncClient):
        """Test API documentation endpoints"""

        response = await client.get("/docs")
        assert response.status_code == 200

        response = await client.get("/redoc")
        assert response.status_code == 200

        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/v1/audio/analyze" in schema["paths"]


@pytest.mark.asyncio
class TestEndToEndScenarios:

    async def test_successful_music_analysis(
        self, client: AsyncClient, mock_audio_analyzer_service
    ):
        """Test successful music file analysis"""

        mock_audio_analyzer_service.analyze_audio.return_value = {
            "duration": 180.5,
            "sample_rate": 44100,
            "channels": 2,
            "bit_depth": 16,
            "file_size": 7500000,
            "format": "mp3",
            "classification": "music",
            "confidence": 0.95,
        }

        response = await client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/song.mp3"}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["classification"] == "music"
        assert data["confidence"] > 0.9
        assert data["duration"] > 180

    async def test_successful_speech_analysis(
        self, client: AsyncClient, mock_audio_analyzer_service
    ):
        """Test successful speech file analysis"""

        mock_audio_analyzer_service.analyze_audio.return_value = {
            "duration": 45.2,
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "file_size": 1440000,
            "format": "wav",
            "classification": "speech",
            "confidence": 0.88,
        }

        response = await client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/podcast.wav"}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["classification"] == "speech"
        assert data["channels"] == 1
        assert data["sample_rate"] == 16000

    async def test_file_too_large_scenario(self, client: AsyncClient, mock_audio_analyzer_service):
        """Test file too large error scenario"""

        mock_audio_analyzer_service.analyze_audio.side_effect = ValueError(
            "Audio too long: 1200.0s"
        )

        response = await client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/very-long-audio.wav"}
        )

        assert response.status_code == 400
        assert "too long" in response.json()["detail"]

    async def test_file_not_found_scenario(self, client: AsyncClient, mock_audio_analyzer_service):
        """Test file not found error scenario"""

        mock_audio_analyzer_service.analyze_audio.side_effect = FileNotFoundError(
            "Audio file not found"
        )

        response = await client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/missing.wav"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    async def test_multiple_format_support(self, client: AsyncClient, mock_audio_analyzer_service):
        """Test support for multiple audio formats"""

        formats = [
            ("test.mp3", "mp3"),
            ("test.wav", "wav"),
            ("test.ogg", "ogg"),
            ("test.m4a", "m4a"),
            ("test.flac", "flac"),
        ]

        for filename, format_type in formats:
            mock_audio_analyzer_service.analyze_audio.return_value = {
                "duration": 30.0,
                "sample_rate": 44100,
                "channels": 2,
                "format": format_type,
                "classification": "music",
                "confidence": 0.8,
            }

            response = await client.post(
                "/v1/audio/analyze", json={"audio_url": f"https://example.com/{filename}"}
            )

            assert response.status_code == 200
            assert response.json()["data"]["format"] == format_type


@pytest.mark.asyncio
class TestPerformanceAndStress:

    async def test_concurrent_requests(self, client: AsyncClient, mock_audio_analyzer_service):
        """Test handling multiple concurrent requests"""

        mock_audio_analyzer_service.analyze_audio.return_value = {
            "duration": 10.0,
            "sample_rate": 44100,
            "channels": 2,
            "classification": "music",
            "confidence": 0.8,
        }

        import asyncio

        async def make_request(url_suffix):
            return await client.post(
                "/v1/audio/analyze", json={"audio_url": f"https://example.com/test{url_suffix}.wav"}
            )

        tasks = [make_request(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)

        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "success"
