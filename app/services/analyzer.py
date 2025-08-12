import os
from typing import Any, Dict

import librosa
from pydub import AudioSegment

from app.config.base import settings
from app.models.audio import AudioFeatures, AudioFormat
from app.repository.cache import CacheRepository
from app.services.classifier import ClassifierService
from app.services.downloader import DownloaderService
from app.services.redis import RedisService


class AudioAnalyzerService:
    def __init__(self, redis_service: RedisService):
        self.cache = CacheRepository(redis_service)
        self.downloader = DownloaderService()
        self.classifier = ClassifierService()

    async def analyze_audio(self, url: str) -> Dict[str, Any]:
        cached = await self.cache.get(url)
        if cached:
            return cached

        temp_path = None
        try:
            metadata = await self.downloader.download(url)
            temp_path = metadata.temp_path

            features = await self._extract_features(temp_path, metadata)
            classification = await self.classifier.classify(temp_path)

            result = {
                "duration": features.duration,
                "sample_rate": features.sample_rate,
                "channels": features.channels,
                "bit_depth": features.bit_depth,
                "file_size": features.file_size,
                "format": features.format.value,
                "classification": classification.classification.value,
                "confidence": classification.confidence,
            }

            await self.cache.set(url, result, settings.CACHE_TTL)
            return result

        finally:
            if temp_path:
                self.downloader.cleanup(temp_path)

    async def _extract_features(self, file_path: str, metadata) -> AudioFeatures:
        try:
            audio = AudioSegment.from_file(file_path)

            duration = len(audio) / 1000.0
            if duration > settings.MAX_DURATION:
                raise ValueError(f"Audio too long: {duration}s")

            return AudioFeatures(
                duration=duration,
                sample_rate=audio.frame_rate,
                channels=audio.channels,
                bit_depth=audio.sample_width * 8 if audio.sample_width else None,
                file_size=metadata.file_size,
                format=self._detect_format(file_path, metadata.content_type),
            )

        except Exception:
            try:
                y, sr = librosa.load(file_path, sr=None)
                duration = len(y) / sr

                if duration > settings.MAX_DURATION:
                    raise ValueError(f"Audio too long: {duration}s")

                return AudioFeatures(
                    duration=duration,
                    sample_rate=sr,
                    channels=1,
                    file_size=metadata.file_size,
                    format=self._detect_format(file_path, metadata.content_type),
                )
            except Exception as e:
                raise ValueError(f"Cannot process audio file: {str(e)}")

    def _detect_format(self, file_path: str, content_type: str) -> AudioFormat:
        ext = os.path.splitext(file_path)[1].lower()

        ext_map = {
            ".mp3": AudioFormat.MP3,
            ".wav": AudioFormat.WAV,
            ".ogg": AudioFormat.OGG,
            ".m4a": AudioFormat.M4A,
            ".flac": AudioFormat.FLAC,
        }

        return ext_map.get(ext, AudioFormat.MP3)
