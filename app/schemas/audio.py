from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class AudioAnalysisRequest(BaseModel):
    audio_url: HttpUrl

    @field_validator("audio_url")
    @classmethod
    def validate_audio_url(cls, v):
        url_str = str(v)
        valid_extensions = [".mp3", ".wav", ".ogg", ".m4a", ".flac"]
        if not any(url_str.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError("Invalid audio file format")
        return v


class AudioAnalysisData(BaseModel):
    duration: float
    sample_rate: int
    channels: int
    bit_depth: Optional[int] = None
    file_size: Optional[int] = None
    format: Optional[str] = None
    classification: Literal["speech", "music", "silence", "noise"]
    confidence: float = Field(ge=0.0, le=1.0)


class AudioAnalysisResponse(BaseModel):
    status: Literal["success", "error"]
    data: Optional[AudioAnalysisData] = None
