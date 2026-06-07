import json
import redis.asyncio as aioredis
from app.core.config import settings

_redis_pool = None

async def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_pool

async def cache_set(key: str, value: dict, ttl: int = 120):
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value))

async def cache_get(key: str) -> dict | None:
    r = await get_redis()
    data = await r.get(key)
    return json.loads(data) if data else None

async def cache_delete(key: str):
    r = await get_redis()
    await r.delete(key)

async def cache_keys(pattern: str) -> list:
    r = await get_redis()
    return await r.keys(pattern)

async def publish(channel: str, message: dict):
    r = await get_redis()
    await r.publish(channel, json.dumps(message))
