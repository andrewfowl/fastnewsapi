import redis.asyncio as aioredis
import logging
import os

logger = logging.getLogger(__name__)
redis_client = None
redisurl = os.getenv("REDIS_URL")

async def init_redis_pool():
    global redis_client
    redis_client = aioredis.Redis(host=redisurl, port=6379)
    logger.info("Redis connection pool created")

async def close_redis_pool():
    await redis_client.close()
    await redis_client.connection_pool.disconnect()
    logger.info("Redis connection pool closed")
