import asyncio
from fastapi import FastAPI, Depends, Query, HTTPException
from redis_client import init_redis_pool, close_redis_pool
from redis.exceptions import ConnectionError, DataError, NoScriptError, RedisError, ResponseError
from redis.commands.search.query import Query as rQuery
from pagination import paginate
from typing import List
import logging

redis_connection=None
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    global redis_connection
    try: 
        redis_connection = await init_redis_pool()
    except Exception as e:
        logger.error(f"Redis connection not initialized on startup. Error: {e}")
    finally:
        pass
    return redis_connection

@app.on_event("shutdown")
async def shutdown_event():
    global redis_connection
    await close_redis_pool(redis_connection)
    return

async def get_redis_connection():
    global redis_connection
    yield redis_connection

@app.get("/rss", response_model=List[str])
async def rss(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    redis=Depends(get_redis_connection)
):
    logger.info(f"Received request for page: {page}, page_size: {page_size}")
    feed_items = []
    q = rQuery("*").paging(page, page_size).sort_by("published", asc=False)
    feed_items = await redis.ft().search(q).docs
    logger.info(f"Values retrieved: {feed_items}")
    # Format the items
    formatted_items = [
            {
                'title': item.get('title', 'No title'),
                'link': item.get('link', 'No link'),
                'published': item.get('published', 'No date'),
                'summary': item.get('summary', 'No summary')
            }
            for feed_item in feed_items
        ]

    return formatted_items

if __name__ == "__main__":
    import hypercorn.asyncio
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:8080"]
    hypercorn.asyncio.run(app, config)
