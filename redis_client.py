import redis.asyncio as aioredis
import logging
import os

logger = logging.getLogger(__name__)
redis_client = None
redisurl = os.getenv("REDIS_URL")

async def init_redis_pool():
    global redis_client
    if redisurl is None:
        logger.error("REDIS_URL environment variable not set")
        return
    try:
        redis_client = aioredis.Redis.from_url(redisurl)
        logger.info(f"Redis connection pool created for {redisurl}")
    except Exception as e:
        logger.error(f"Error creating Redis connection pool: {e}")

async def close_redis_pool():
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        await redis_client.connection_pool.disconnect()
        logger.info("Redis connection pool closed")
    else:
        logger.error("Redis client is not initialized")
