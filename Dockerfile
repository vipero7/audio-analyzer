FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NUMBA_CACHE_DIR=/tmp/numba_cache

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python -m pytest tests/ -v --cov=app --cov-fail-under=70

RUN useradd appuser
RUN mkdir -p /tmp/numba_cache /app/app/logs && chown -R appuser:appuser /app /tmp/numba_cache
USER appuser

EXPOSE 8000
CMD ["python", "asgi.py"]