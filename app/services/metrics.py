from prometheus_client import Counter, Histogram


class MetricsService:
    def __init__(self):
        self.requests_total = Counter("audio_requests_total", "Total requests")
        self.processing_duration = Histogram("audio_processing_duration_seconds", "Processing time")
        self.errors_total = Counter("audio_errors_total", "Total errors", ["error_type"])

    def record_request(self):
        self.requests_total.inc()

    def record_error(self, error_type: str):
        self.errors_total.labels(error_type=error_type).inc()
