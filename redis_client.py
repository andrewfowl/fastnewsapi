import redis.asyncio as aioredis
import logging
import os

logger = logging.getLogger(__name__)
redis_url = os.getenv("REDIS_PRIVATE_URL")
redis_port = os.getenv("REDISPORT")
redis_host = os.getenv("REDISHOST")
redis_pass = os.getenv("REDIS_PASSWORD")

redis_client = redis.StrictRedis(
        host=redis_host,
        port=redis_port,
        password=redis_pass,
        decode_responses=True
    )

async def init_redis_pool():
    global redis_client
    if redis_url is None:
        logger.error("REDIS_PRIVATE_URL environment variable not set")
        return None
    try:
        redis_client = aioredis.from_url(redis_url)
        # Test the connection to ensure it's set up properly
        await redis_client.ping()
        logger.info(f"Redis client created for {redis_url}")
        return redis_client
    except Exception as e:
        logger.error(f"Error creating Redis client: {e}")
        redis_client = None
        return None

async def close_redis_pool():
    global redis_client
    if redis_client is not None:
        try:
            await redis_client.close()
            await redis_client.connection_pool.disconnect()
            logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection pool: {e}")
    else:
        logger.warning("Redis client was not initialized, nothing to close")
