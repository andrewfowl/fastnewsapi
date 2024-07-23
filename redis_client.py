import aioredis
from fastapi import FastAPI
import logging
import os

logger = logging.getLogger(__name__)
redis = None
redisurl=os.getenv("REDIS_URL")

async def init_redis_pool():
    global redis
    redis = await aioredis.create_redis_pool(
        redisurl, minsize=5, maxsize=10
    )
    logger.info("Redis connection pool created")

async def close_redis_pool():
    redis.close()
    await redis.wait_closed()
    logger.info("Redis connection pool closed")
