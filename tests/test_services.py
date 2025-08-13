from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.audio import AudioFormat, DownloadMetadata
from app.services.analyzer import AudioAnalyzerService
from app.services.classifier import ClassifierService
from app.services.downloader import DownloaderService
from app.services.redis import RedisService


@pytest.mark.asyncio
class TestRedisService:

    @pytest.fixture
    def redis_service(self):
        return RedisService()

    async def test_connect_success(self, redis_service):
        with patch("app.services.redis.redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.from_url.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = True

            await redis_service.connect()

            assert redis_service.is_connected() is True
            mock_redis_instance.ping.assert_called_once()

    async def test_connect_failure(self, redis_service):
        with patch("app.services.redis.redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.from_url.return_value = mock_redis_instance
            mock_redis_instance.ping.side_effect = Exception("Connection failed")

            with pytest.raises(Exception):
                await redis_service.connect()

            assert redis_service.is_connected() is False

    async def test_get_when_connected(self, redis_service):
        redis_service._connected = True
        redis_service.redis = AsyncMock()
        redis_service.redis.get.return_value = "test_value"

        result = await redis_service.get("test_key")
        assert result == "test_value"

    async def test_get_when_disconnected(self, redis_service):
        redis_service._connected = False

        result = await redis_service.get("test_key")
        assert result is None

    async def test_setex_success(self, redis_service):
        redis_service._connected = True
        redis_service.redis = AsyncMock()
        redis_service.redis.setex.return_value = True

        result = await redis_service.setex("test_key", 60, "test_value")
        assert result is True


@pytest.mark.asyncio
class TestAudioAnalyzerService:

    @pytest.fixture
    def mock_redis_service(self):
        mock_redis = AsyncMock()
        mock_redis.is_connected.return_value = True
        return mock_redis

    @pytest.fixture
    def analyzer_service(self, mock_redis_service):
        return AudioAnalyzerService(mock_redis_service)

    async def test_analyze_audio_cache_hit(self, analyzer_service, sample_audio_data):
        analyzer_service.cache.get = AsyncMock(return_value=sample_audio_data)

        result = await analyzer_service.analyze_audio("https://example.com/test.wav")

        assert result == sample_audio_data
        analyzer_service.cache.get.assert_called_once()

    async def test_analyze_audio_cache_miss(self, analyzer_service):
        analyzer_service.cache.get = AsyncMock(return_value=None)
        analyzer_service.cache.set = AsyncMock(return_value=True)
        analyzer_service.downloader.download = AsyncMock()
        analyzer_service.downloader.cleanup = MagicMock()

        with patch.object(analyzer_service, "extract_features") as mock_extract:
            with patch.object(analyzer_service.classifier, "classify") as mock_classify:
                mock_extract.return_value = MagicMock(
                    duration=5.0,
                    sample_rate=44100,
                    channels=2,
                    bit_depth=16,
                    file_size=1000,
                    format=AudioFormat.WAV,
                )
                mock_classify.return_value = MagicMock(
                    classification=MagicMock(value="music"), confidence=0.9
                )

                result = await analyzer_service.analyze_audio("https://example.com/test.wav")

                assert result["duration"] == 5.0
                assert result["classification"] == "music"
                analyzer_service.cache.set.assert_called_once()

    async def test_detect_format_from_extension(self, analyzer_service):
        result = analyzer_service.detect_format("/tmp/test.mp3", "audio/mpeg")
        assert result == AudioFormat.MP3

        result = analyzer_service.detect_format("/tmp/test.wav", "audio/wav")
        assert result == AudioFormat.WAV


class TestDownloaderService:

    @pytest.fixture
    def downloader_service(self):
        return DownloaderService()

    @pytest.mark.asyncio
    async def test_download_success(self, downloader_service):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.headers = {"content-type": "audio/wav"}
            mock_response.content = b"fake audio content"
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = mock_client.return_value.__aenter__.return_value
            mock_client_instance.get.return_value = mock_response

            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                mock_temp.return_value.name = "/tmp/test.wav"
                mock_temp.return_value.close = MagicMock()

                with patch("aiofiles.open"):
                    with patch("os.path.getsize", return_value=1000):
                        result = await downloader_service.download("https://example.com/test.wav")

                        assert isinstance(result, DownloadMetadata)
                        assert result.url == "https://example.com/test.wav"
                        assert result.content_type == "audio/wav"
                        assert result.file_size == 1000

    def test_get_extension_from_url(self, downloader_service):
        result = downloader_service._get_extension("https://example.com/test.mp3", "")
        assert result == ".mp3"

    def test_get_extension_from_content_type(self, downloader_service):
        result = downloader_service._get_extension("https://example.com/test", "audio/mpeg")
        assert result == ".mp3"

    def test_get_extension_default(self, downloader_service):
        result = downloader_service._get_extension("https://example.com/test", "unknown/type")
        assert result == ".mp3"


class TestClassifierService:

    @pytest.fixture
    def classifier_service(self):
        return ClassifierService()

    @pytest.mark.asyncio
    async def test_classify_audio_success(self, classifier_service):
        with patch("librosa.load") as mock_load:
            mock_load.return_value = ([0.1, 0.2, 0.3], 22050)

            with patch.object(classifier_service, "extract_features") as mock_extract:
                mock_extract.return_value = {
                    "rms": 0.1,
                    "zcr": 0.1,
                    "spectral_centroid": 2000,
                    "tempo": 120,
                    "harmonic_ratio": 0.7,
                }

                result = await classifier_service.classify("/tmp/test.wav")

                assert result.classification.value in ["speech", "music", "silence", "noise"]
                assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_classify_audio_error_fallback(self, classifier_service):
        with patch("librosa.load", side_effect=Exception("Load failed")):
            result = await classifier_service.classify("/tmp/test.wav")

            assert result.classification.value == "noise"
            assert result.confidence == 0.5

    def test_classify_features_silence(self, classifier_service):
        features = {
            "rms": 0.005,
            "zcr": 0.1,
            "spectral_centroid": 1000,
            "tempo": 0,
            "harmonic_ratio": 0.3,
        }
        classification, confidence = classifier_service.classify_features(features)

        assert classification == "silence"
        assert confidence >= 0.9

    def test_classify_features_music(self, classifier_service):
        features = {
            "rms": 0.1,
            "zcr": 0.1,
            "spectral_centroid": 2500,
            "tempo": 120,
            "harmonic_ratio": 0.7,
        }
        classification, confidence = classifier_service.classify_features(features)

        assert classification == "music"
        assert confidence > 0.5
