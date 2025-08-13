import hashlib
import json
from typing import Any, Dict, Optional

from app.services.redis import RedisService


class CacheRepository:
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service

    def generate_key(self, url: str) -> str:
        hash_value = hashlib.sha256(url.encode()).hexdigest()[:16]
        return f"audio:{hash_value}"

    async def get(self, url: str) -> Optional[Dict[str, Any]]:
        if not self.redis.is_connected():
            return None

        key = self.generate_key(url)
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set(self, url: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        if not self.redis.is_connected():
            return False

        try:
            key = self.generate_key(url)
            return await self.redis.setex(key, ttl, json.dumps(data))
        except Exception:
            return False
