from uuid import UUID

from app.redis_client import redis_client

RATE_LIMIT = 10
WINDOW_SEC = 60


async def check_rate_limit(source_id: UUID) -> bool:
    key = f"rate_limit:{source_id}"

    count = await redis_client.incr(key)

    if count == 1:
        await redis_client.expire(key, WINDOW_SEC)

    return count <= RATE_LIMIT
