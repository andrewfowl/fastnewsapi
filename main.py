import os
import asyncio
from fastapi import FastAPI, Query, HTTPException
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import ConnectionError, DataError, NoScriptError, RedisError, ResponseError
from redis.commands.search.query import Query as rQuery
from typing import List
import logging

redis_url = os.getenv("REDIS_URL")
redis_port = int(os.getenv("REDISPORT", 6379))
redis_host = os.getenv("REDISHOST")
redis_pass = os.getenv("REDIS_PASSWORD")

# Initialize Redis pool using redis.asyncio for asyncio compatibility
redis_pool = ConnectionPool.from_url(redis_url, decode_responses=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    global redis_pool, redis_client
    redis_client = Redis(connection_pool=redis_pool)
    test_connection = await redis_client.ping()
    logger.info(f"Redis client initialized: {test_connection}")

@app.on_event("shutdown")
async def shutdown_event():
    global redis_pool, redis_client
    await redis_client.close()
    await redis_pool.disconnect()
    logger.info("Redis client closed")

@app.get("/rss", response_model=List[str])
async def rss(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    logger.info(f"Received request for page: {page}, page_size: {page_size}")
    try:
        start = (page - 1) * page_size
        end = start + page_size - 1

        # Use a sorted set for pagination
        feed_ids = await redis_client.zrevrange('rss_feed', start, end)

        # Fetch all items by their IDs asynchronously
        async def get_feed_item(feed_id):
            return await redis_client.hgetall(f'rss_feed_item:{feed_id}')

        tasks = [get_feed_item(feed_id) for feed_id in feed_ids]
        feed_items = await asyncio.gather(*tasks)

        logger.info(f"Values retrieved: {feed_items}")
        return feed_items
    except (ConnectionError, DataError, RedisError, ResponseError) as e:
        logger.error(f"Redis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import hypercorn
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:8080"]
    asyncio.run(hypercorn.asyncio.serve(app, config))
