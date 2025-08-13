from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AudioFormat(str, Enum):
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    M4A = "m4a"
    FLAC = "flac"


class AudioClassification(str, Enum):
    SPEECH = "speech"
    MUSIC = "music"
    SILENCE = "silence"
    NOISE = "noise"


class DownloadMetadata(BaseModel):
    url: str
    content_type: str
    file_size: int
    temp_path: str


class AudioFeatures(BaseModel):
    duration: float
    sample_rate: int
    channels: int
    bit_depth: Optional[int] = None
    file_size: int
    format: AudioFormat


class ClassificationResult(BaseModel):
    classification: AudioClassification
    confidence: float
