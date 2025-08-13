from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_audio_analyzer_service, get_metrics_service
from app.config.logger import get_logger
from app.schemas.audio import AudioAnalysisRequest, AudioAnalysisResponse
from app.services.analyzer import AudioAnalyzerService
from app.services.metrics import MetricsService

logger = get_logger(__name__)
api_router = APIRouter()


@api_router.get("/metrics/test")
async def test_metrics(metrics: MetricsService = Depends(get_metrics_service)):
    metrics.record_request()
    metrics.record_error("test")
    return {"message": "Metrics recorded", "check": "http://localhost:8001/metrics"}


@api_router.post("/audio/analyze", response_model=AudioAnalysisResponse)
async def analyze_audio(
    request: AudioAnalysisRequest,
    analyzer: AudioAnalyzerService = Depends(get_audio_analyzer_service),
    metrics: MetricsService = Depends(get_metrics_service),
) -> AudioAnalysisResponse:
    metrics.record_request()

    try:
        logger.info(f"Analyzing audio: {request.audio_url}")

        with metrics.processing_duration.time():
            result = await analyzer.analyze_audio(str(request.audio_url))

        logger.info("Analysis completed successfully")
        return AudioAnalysisResponse(status="success", data=result)

    except ValueError as e:
        metrics.record_error("validation")
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        metrics.record_error("not_found")
        logger.error("Audio file not found")
        raise HTTPException(status_code=404, detail="Audio file not found")
    except Exception as e:
        metrics.record_error("internal")
        logger.error(f"Internal error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
