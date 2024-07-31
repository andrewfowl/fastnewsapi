import redis
import logging
import os

logger = logging.getLogger(__name__)
redis_client = None
redisurl = os.getenv("REDIS_PRIVATE_URL")

async def init_redis_pool():
    global redis_client
    if redisurl is None:
        logger.error("REDIS_PRIVATE_URL environment variable not set")
        return
    try:
        redis_client = redis.Redis(host=redisurl, port=6379, db=1)
        # Test the connection to ensure it's set up properly
        await redis_client.ping()
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
