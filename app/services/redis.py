from typing import Optional

import redis.asyncio as redis

from app.config.base import settings


class RedisService:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self._connected = False

    async def connect(self):
        try:
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.redis.ping()

            await self.redis.config_set("maxmemory", settings.CACHE_MAX_MEMORY)
            await self.redis.config_set("maxmemory-policy", settings.CACHE_POLICY)

            self._connected = True
        except Exception as e:
            self._connected = False
            raise e

    async def close(self):
        if self.redis:
            try:
                await self.redis.close()
            except Exception:
                pass
            self._connected = False

    def is_connected(self) -> bool:
        return self._connected and self.redis is not None

    async def get(self, key: str) -> Optional[str]:
        if not self.is_connected():
            return None
        try:
            return await self.redis.get(key)
        except Exception:
            return None

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        if not self.is_connected():
            return False
        try:
            result = await self.redis.setex(key, ttl, value)
            return result is True
        except Exception:
            return False
