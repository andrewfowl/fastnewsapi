import asyncio
import redis.asyncio as redis
import logging
import os

logger = logging.getLogger(__name__)


async def init_redis_pool():
    redis_url = os.getenv("REDIS_URL")
    redis_port = os.getenv("REDISPORT")
    redis_host = os.getenv("REDISHOST")
    redis_pass = os.getenv("REDIS_PASSWORD")
    try:
        redis_pool = redis.ConnectionPool(host=redis_host,port=redis_port,password=redis_pass,decode_responses=True)
        redis_connection = redis.StrictRedis(connection_pool=redis_pool)
        logger.info(f"Redis client created for {redis_url}")
        test_connection = await redis_connection.ping()
        logger.info(f"Redis connection test: {test_connection}")
        return redis_connection
    except Exception as e:
        logger.error(f"Error creating Redis client: {e}")

async def close_redis_pool(redis_connection):
    if redis_connection:
        try:
            await redis_connection.close()
            logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection pool: {e}")
