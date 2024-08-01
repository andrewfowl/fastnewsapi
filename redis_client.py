import redis
import logging
import os

logger = logging.getLogger(__name__)
redis_url = os.getenv("REDIS_URL")
redis_port = os.getenv("REDISPORT")
redis_host = os.getenv("REDISHOST")
redis_pass = os.getenv("REDIS_PASSWORD")
redis_client = None

def init_redis_pool():
    global redis_client
    try:
        redis_client = redis.StrictRedis(
        host=redis_host,
        port=redis_port,
        password=redis_pass,
        decode_responses=True,
        ssl_cert_reqs=none,
        health_check_interval=2
    )
        logger.info(f"Redis client created for {redis_url}")
        return redis_client
    except Exception as e:
        logger.error(f"Error creating Redis client: {e}")

def close_redis_pool():
    global redis_client
    if redis_client is None:
        logger.warning("Redis client was not initialized, nothing to close")
    else:
        try:
            redis_client.close()
            logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection pool: {e}")
