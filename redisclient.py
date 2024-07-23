import aioredis
from fastapi import FastAPI

redis = None
redisurl=os.get("REDIS_URL")

async def init_redis_pool():
    global redis
    redis = await aioredis.create_redis_pool(
        'redis://localhost', minsize=5, maxsize=10
    )

async def close_redis_pool():
    redis.close()
    await redis.wait_closed()
