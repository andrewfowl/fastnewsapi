import asyncio
from fastapi import FastAPI, Depends, Query, HTTPException
from redis_client import init_redis_pool, close_redis_pool
from redis.exceptions import ConnectionError, DataError, NoScriptError, RedisError, ResponseError
from redis.commands.search.query import Query as rQuery
from pagination import paginate
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
redis_connection = redis_client.redis_connection

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await init_redis_pool()

@app.on_event("shutdown")
async def shutdown_event():
    await close_redis_pool()

def get_redis_connection():
    try:
        yield redis_connection
    except Exception as e:
        logger.error(f"Redis connection not initialized when accessed. Error: {e}")
    finally:
        pass

@app.get("/rss", response_model=List[str])
async def rss(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    redis=Depends(get_redis_connection)
):
    logger.info(f"Received request for page: {page}, page_size: {page_size}")
    feed_items = []
    q = rQuery("*").paging(page, page_size).sort_by("published", asc=False)
    feed_items = redis.ft().search(q).docs
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
