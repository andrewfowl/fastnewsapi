import redis.asyncio as aioredis
import logging
import os

logger = logging.getLogger(__name__)
redis_url = os.getenv("REDIS_PRIVATE_URL")

async def init_redis_pool():
    if redis_url is None:
        logger.error("REDIS_PRIVATE_URL environment variable not set")
        return
    try:
        redis_client = aioredis.from_url(redis_url)
        # Test the connection to ensure it's set up properly
        await redis_client.ping()
        logger.info(f"Redis client created for {redis_url}")
    except Exception as e:
        logger.error(f"Error creating Redis client: {e}")

async def close_redis_pool():
    if redis_client is not None:
        await redis_client.close()
        await redis_client.connection_pool.disconnect()
        logger.info("Redis connection pool closed")
    else:
        return
