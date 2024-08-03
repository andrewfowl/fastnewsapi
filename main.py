from fastapi import FastAPI, Depends, Query, HTTPException
from redis_client import init_redis_pool, close_redis_pool, redis_client
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
def shutdown_event():
    close_redis_pool()

def get_redis():
    try:
        return redis_client
    except Exception as e:
        logger.error("Redis client not initialized when accessed")

def get_redis_connection(redis=Depends(get_redis)):
    try:
        yield redis
    finally:
        pass  

@app.get("/rss", response_model=List[str])
def get_data(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    redis=Depends(get_redis_connection)
):
    logger.info(f"Received request for page: {page}, page_size: {page_size}")

    try:
        keys = redis_client.smembers('rss_links')
        feed_items = [redis_client.hgetall(f"rss_item:{key}") for key in keys]
        logger.info(f"Values retrieved: {feed_items}")
    except Exception as e:
        logger.error(f"Error fetching data from Redis: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    
    paginated_values = paginate(feed_items, page, page_size)
    logger.debug(f"Paginated values: {paginated_values}")
    
    return paginated_values

if __name__ == "__main__":
    import hypercorn.asyncio
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:8080"]
    hypercorn.asyncio.run(app, config)
