import librosa
import numpy as np

from app.models.audio import AudioClassification, ClassificationResult


class ClassifierService:
    def __init__(self):
        self.sr = 22050

    async def classify(self, file_path: str) -> ClassificationResult:
        try:
            y, sr = librosa.load(file_path, sr=self.sr, duration=30.0)
            features = self.extract_features(y, sr)
            classification, confidence = self.classify_features(features)

            return ClassificationResult(
                classification=AudioClassification(classification), confidence=confidence
            )
        except Exception:
            return ClassificationResult(classification=AudioClassification.NOISE, confidence=0.5)

    def extract_features(self, y: np.ndarray, sr: int) -> dict:
        features = {}

        features["rms"] = float(np.sqrt(np.mean(y**2)))
        features["zcr"] = float(np.mean(librosa.feature.zero_crossing_rate(y)))

        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        features["spectral_centroid"] = float(np.mean(spectral_centroids))

        try:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            features["tempo"] = float(tempo)
        except Exception:
            features["tempo"] = 0.0

        y_harmonic, y_percussive = librosa.effects.hpss(y)
        features["harmonic_ratio"] = float(np.sum(y_harmonic**2) / (np.sum(y**2) + 1e-8))

        return features

    def classify_features(self, features: dict) -> tuple[str, float]:
        if features["rms"] < 0.01:
            return AudioClassification.SILENCE.value, 0.95

        if features["rms"] < 0.02:
            return AudioClassification.NOISE.value, 0.75

        music_score = 0.0
        speech_score = 0.0

        if features["tempo"] > 60:
            music_score += 0.3

        if features["harmonic_ratio"] > 0.6:
            music_score += 0.3

        if 0.05 < features["zcr"] < 0.2:
            speech_score += 0.4

        if features["spectral_centroid"] < 2000:
            speech_score += 0.2

        if music_score > speech_score and music_score > 0.3:
            return AudioClassification.MUSIC.value, min(0.95, 0.5 + music_score)
        elif speech_score > 0.3:
            return AudioClassification.SPEECH.value, min(0.95, 0.5 + speech_score)
        else:
            return AudioClassification.NOISE.value, 0.6
