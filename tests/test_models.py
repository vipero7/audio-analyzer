import pytest
from pydantic import ValidationError

from app.models.audio import (
    AudioClassification,
    AudioFeatures,
    AudioFormat,
    DownloadMetadata,
)
from app.schemas.audio import (
    AudioAnalysisData,
    AudioAnalysisRequest,
    AudioAnalysisResponse,
)


class TestAudioModels:

    def test_audio_format_enum(self):
        assert AudioFormat.MP3 == "mp3"
        assert AudioFormat.WAV == "wav"
        assert AudioFormat.OGG == "ogg"
        assert AudioFormat.M4A == "m4a"
        assert AudioFormat.FLAC == "flac"

    def test_audio_classification_enum(self):
        assert AudioClassification.SPEECH == "speech"
        assert AudioClassification.MUSIC == "music"
        assert AudioClassification.SILENCE == "silence"
        assert AudioClassification.NOISE == "noise"

    def test_download_metadata_creation(self):
        metadata = DownloadMetadata(
            url="https://example.com/test.wav",
            content_type="audio/wav",
            file_size=1000,
            temp_path="/tmp/test.wav",
        )

        assert metadata.url == "https://example.com/test.wav"
        assert metadata.content_type == "audio/wav"
        assert metadata.file_size == 1000
        assert metadata.temp_path == "/tmp/test.wav"

    def test_audio_features_creation(self):
        features = AudioFeatures(
            duration=5.0,
            sample_rate=44100,
            channels=2,
            bit_depth=16,
            file_size=1000,
            format=AudioFormat.WAV,
        )

        assert features.duration == 5.0
        assert features.sample_rate == 44100
        assert features.channels == 2
        assert features.format == AudioFormat.WAV

    def test_audio_features_validation(self):
        with pytest.raises(ValidationError):
            AudioFeatures(
                duration=-1.0,
                sample_rate=44100,
                channels=2,
                file_size=1000,
                format=AudioFormat.WAV,
            )

        with pytest.raises(ValidationError):
            AudioFeatures(
                duration=5.0,
                sample_rate=0,
                channels=2,
                file_size=1000,
                format=AudioFormat.WAV,
            )

        with pytest.raises(ValidationError):
            AudioFeatures(
                duration=5.0,
                sample_rate=44100,
                channels=0,
                file_size=1000,
                format=AudioFormat.WAV,
            )


class TestAudioSchemas:

    def test_audio_analysis_request_valid_urls(self):
        valid_urls = [
            "https://example.com/test.mp3",
            "https://example.com/test.wav",
            "https://example.com/test.ogg",
            "https://example.com/test.m4a",
            "https://example.com/test.flac",
        ]

        for url in valid_urls:
            request = AudioAnalysisRequest(audio_url=url)
            assert str(request.audio_url) == url

    def test_audio_analysis_request_invalid_format(self):
        with pytest.raises(ValidationError) as exc_info:
            AudioAnalysisRequest(audio_url="https://example.com/test.txt")

        assert "Invalid audio file format" in str(exc_info.value)

    def test_audio_analysis_request_invalid_url(self):
        with pytest.raises(ValidationError):
            AudioAnalysisRequest(audio_url="not-a-url")

    def test_audio_analysis_data_creation(self):
        data = AudioAnalysisData(
            duration=5.0,
            sample_rate=44100,
            channels=2,
            bit_depth=16,
            file_size=1000,
            format="wav",
            classification="music",
            confidence=0.9,
        )

        assert data.duration == 5.0
        assert data.classification == "music"
        assert data.confidence == 0.9

    def test_audio_analysis_data_confidence_validation(self):
        with pytest.raises(ValidationError):
            AudioAnalysisData(
                duration=5.0,
                sample_rate=44100,
                channels=2,
                classification="music",
                confidence=1.5,
            )

        with pytest.raises(ValidationError):
            AudioAnalysisData(
                duration=5.0,
                sample_rate=44100,
                channels=2,
                classification="music",
                confidence=-0.1,
            )

    def test_audio_analysis_response_success(self):
        data = AudioAnalysisData(
            duration=5.0, sample_rate=44100, channels=2, classification="music", confidence=0.9
        )

        response = AudioAnalysisResponse(status="success", data=data)

        assert response.status == "success"
        assert response.data.classification == "music"

    def test_audio_analysis_response_error(self):
        response = AudioAnalysisResponse(status="error", data=None)

        assert response.status == "error"
        assert response.data is None

    def test_audio_analysis_response_serialization(self):
        data = AudioAnalysisData(
            duration=5.0, sample_rate=44100, channels=2, classification="music", confidence=0.9
        )

        response = AudioAnalysisResponse(status="success", data=data)
        json_data = response.model_dump()

        assert json_data["status"] == "success"
        assert json_data["data"]["classification"] == "music"
        assert json_data["data"]["confidence"] == 0.9
