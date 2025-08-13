from fastapi.testclient import TestClient


class TestHealthEndpoints:

    def test_main_health_endpoint(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "Audio Analyzer API" in data["message"]


class TestAudioAnalysisEndpoints:

    def test_analyze_audio_success(self, client: TestClient):
        response = client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/test.wav"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["classification"] == "music"
        assert data["data"]["duration"] == 5.23
        assert data["data"]["sample_rate"] == 44100

    def test_analyze_audio_with_different_formats(self, client: TestClient, valid_audio_urls):
        for url in valid_audio_urls:
            response = client.post("/v1/audio/analyze", json={"audio_url": url})
            assert response.status_code == 200
            assert response.json()["status"] == "success"

    def test_analyze_audio_invalid_format(self, client: TestClient):
        response = client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/test.txt"}
        )
        assert response.status_code == 422

    def test_analyze_audio_malformed_url(self, client: TestClient):
        response = client.post("/v1/audio/analyze", json={"audio_url": "not-a-url"})
        assert response.status_code == 422

    def test_analyze_audio_missing_url(self, client: TestClient):
        response = client.post("/v1/audio/analyze", json={})
        assert response.status_code == 422

    def test_analyze_audio_file_not_found(self, client: TestClient, mock_audio_analyzer_service):
        mock_audio_analyzer_service.analyze_audio.side_effect = FileNotFoundError("File not found")

        response = client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/nonexistent.wav"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_analyze_audio_validation_error(self, client: TestClient, mock_audio_analyzer_service):
        mock_audio_analyzer_service.analyze_audio.side_effect = ValueError("Invalid audio file")

        response = client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/invalid.wav"}
        )
        assert response.status_code == 400
        assert "Invalid audio file" in response.json()["detail"]

    def test_analyze_audio_internal_error(self, client: TestClient, mock_audio_analyzer_service):
        mock_audio_analyzer_service.analyze_audio.side_effect = Exception("Unexpected error")

        response = client.post(
            "/v1/audio/analyze", json={"audio_url": "https://example.com/test.wav"}
        )
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestMetricsEndpoints:

    def test_prometheus_metrics_endpoint(self, client: TestClient):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


class TestAPIDocumentation:

    def test_openapi_docs(self, client: TestClient):
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_docs(self, client: TestClient):
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_schema(self, client: TestClient):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "/v1/audio/analyze" in schema["paths"]
