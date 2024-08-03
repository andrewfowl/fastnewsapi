import asyncio
import redis.asyncio as redis
import logging
import os

logger = logging.getLogger(__name__)
redis_url = os.getenv("REDIS_URL")
redis_port = os.getenv("REDISPORT")
redis_host = os.getenv("REDISHOST")
redis_pass = os.getenv("REDIS_PASSWORD")
redis_pool = redis.ConnectionPool(
            host=redis_host,
            port=redis_port,
            password=redis_pass,
            decode_responses=True,
            ssl_cert_reqs=none
        )
redis_connection = None

def init_redis_pool():
    global redis_connection, redis_pool
    try:
        redis_connection = redis.StrictRedis(connection_pool=redis_pool)
        logger.info(f"Redis client created for {redis_url}")
    except Exception as e:
        logger.error(f"Error creating Redis client: {e}")

async def close_redis_pool():
    global redis_connection, redis_pool
    try:
        await redis_connection.aclose()
        await redis_pool.aclose()
        logger.info("Redis connection pool closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection pool: {e}")
