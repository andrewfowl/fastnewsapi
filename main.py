import asyncio
from fastapi import FastAPI, Depends, Query, HTTPException
from redis_client import init_redis_pool, close_redis_pool
from pagination import paginate
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
def startup_event():
    init_redis_pool()

@app.on_event("shutdown")
async def shutdown_event():
    await close_redis_pool()

def get_redis():
    try:
        return redis_client.redis_connection
    except Exception as e:
        logger.error(f"Redis connection not initialized when accessed. Error: {e}")

def get_redis_connection(redis=Depends(get_redis)):
    try:
        yield redis
    finally:
        pass  

class News(SQLModel):
    title: str = Field(default=None, nullable=True)
    link: str = Field(default=None, nullable=True)
    published: date = Field(default=None, nullable=True)
    summary: str = Field(default=None, nullable=True)

@app.get("/rss", response_model=List[str])
async def rss(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    redis=Depends(get_redis_connection)
):
    logger.info(f"Received request for page: {page}, page_size: {page_size}")

    schema = (TextField("$.title", as_name="name"), TextField("$.link", as_name="link"), TextField("$.published", as_name="published"), TextField("$.summary", as_name="summary"))
    redis.ft().create_index(schema, definition=IndexDefinition(prefix=["news:"], index_type=IndexType.JSON))
    q = Query("*").paging(page, page_size).sort_by("published", asc=False)
    feed_items = []
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
