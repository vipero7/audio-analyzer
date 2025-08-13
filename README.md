# Audio Analyzer & Classifier API

A FastAPI-based microservice that analyzes and classifies audio files asynchronously. The service downloads audio files from URLs, extracts features, and classifies them as speech, music, silence, or noise with Redis caching support.

## Features

- **Async Audio Processing**: Downloads and processes audio files asynchronously
- **Audio Classification**: Classifies audio as speech, music, silence, or noise
- **Feature Extraction**: Extracts duration, sample rate, channels, and format information
- **Redis Caching**: Caches analysis results to improve performance
- **Prometheus Metrics**: Built-in metrics for monitoring
- **Comprehensive Testing**: Full test suite with coverage reporting
- **Docker Support**: Containerized deployment with health checks

## Prerequisites

### System Requirements
- Python 3.10+
- Redis Server
- FFmpeg (for audio processing)

### Installing Redis

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS (with Homebrew):**
```bash
brew install redis
brew services start redis
```

**Configure Redis for Docker Access:**
```bash
# Edit Redis configuration
sudo nano /etc/redis/redis.conf

# Find the line: bind 127.0.0.1 ::1
# Change it to: bind 0.0.0.0

# Restart Redis
sudo systemctl restart redis-server

# Verify Redis is running and accessible
redis-cli ping
# Should return: PONG

# Verify bind configuration
redis-cli config get bind
# Should return: 0.0.0.0
```

## Project Structure

```
audio-analyzer/
├── app/
│   ├── api/
│   │   ├── dependencies.py      # Dependencies
│   │   └── v1/
│   │       └── router.py        # API routes
│   ├── config/
│   │   ├── base.py             # Settings and configuration
│   │   └── logger.py           # Logging configuration
│   ├── models/
│   │   └── audio.py            # Data models
│   ├── repository/
│   │   └── cache.py            # Cache operations
│   ├── schemas/
│   │   └── audio.py            # Pydantic schemas
│   ├── services/
│   │   ├── analyzer.py         # Audio analysis service
│   │   ├── classifier.py       # Audio classification
│   │   ├── downloader.py       # Async file downloader
│   │   ├── metrics.py          # Prometheus metrics
│   │   └── redis.py            # Redis service
│   └── main.py                 # FastAPI application factory
├── tests/                      # Test suite
├── .env                        # Environment variables
├── asgi.py                     # Application entry point
├── Dockerfile                  # Docker configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Setup Instructions

### 1. Clone and Setup Environment

```bash
git clone git@github.com:vipero7/audio-analyzer.git
cd audio-analyzer

# Create virtual environment
python -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
# If this produces error install with uv
pip install uv
uv pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in project root:

```bash
ENV=local
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_RELOAD=false

REDIS_URL=redis://localhost:6379
CACHE_TTL=3600
DOWNLOAD_TIMEOUT=30
MAX_FILE_SIZE=104857600
MAX_DURATION=600
TEMP_DIR=/tmp
CACHE_MAX_MEMORY=256mb
CACHE_POLICY=allkeys-lru
```

### 3. Start Redis Server

```bash
# Linux/macOS
redis-server

# Verify Redis is running
redis-cli ping
```

## Running the Application

### Option 1: Run Locally

```bash
python asgi.py
```

### Option 2: Run with Docker

```bash
# Build the image
docker build -t audio-analyzer .

# Run with host Redis
docker run -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  --env-file .env \
  audio-analyzer

# Update REDIS_URL in .env file
REDIS_URL=redis://host.docker.internal:6379
```

## API Usage

### Analyze Audio

**Endpoint:** `POST /api/v1/analyze-audio`

**Request:**
```json
{
  "audio_url": "https://example.com/audio/sample.wav"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "duration": 5.23,
    "sample_rate": 44100,
    "channels": 2,
    "classification": "music",
    "format": "wav",
    "file_size": 461340
  }
}
```

**Example with cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze-audio" \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "https://example.com/audio/test.wav"}'
```

### Health Check

```bash
curl http://localhost:8000/health
```

### API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

Coverage reports are generated in `htmlcov/` directory.

## Monitoring

### Prometheus Metrics

Metrics are available at: http://localhost:8000/metrics

### Logs

Application logs are written to console and `app/logs/app.log`.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENV` | Environment | local |
| `FASTAPI_HOST` | Host to bind to | 0.0.0.0 |
| `FASTAPI_PORT` | Port to bind to | 8000 |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379 |
| `CACHE_TTL` | Cache TTL in seconds | 3600 |
| `DOWNLOAD_TIMEOUT` | Download timeout in seconds | 30 |
| `MAX_FILE_SIZE` | Max file size in bytes | 104857600 |
| `MAX_DURATION` | Max audio duration in seconds | 600 |

### Audio Format Support

Supported formats: WAV, MP3, FLAC, OGG, M4A, AIFF

## License

MIT License - see LICENSE file for details.