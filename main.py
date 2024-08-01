from fastapi import FastAPI, Depends, Query, HTTPException
from redis_client import init_redis_pool, close_redis_pool
from pagination import paginate
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await init_redis_pool()

@app.on_event("shutdown")
async def shutdown_event():
    await close_redis_pool()

async def get_redis():
    if not redis_client:
        logger.error("Redis client not initialized when accessed")
        raise HTTPException(status_code=500, detail="Redis client not initialized")
    return redis_client

async def get_redis_connection(redis=Depends(get_redis)):
    try:
        yield redis
    finally:
        pass  

@app.get("/rss", response_model=List[str])
async def get_data(
    keys: List[str] = Query(..., description="List of Redis keys to retrieve"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    redis=Depends(get_redis_connection)
):
    logger.info(f"Received request for keys: {keys}, page: {page}, page_size: {page_size}")

    try:
        values = await redis.mget(keys)
        logger.info(f"Values retrieved: {values}")
    except Exception as e:
        logger.error(f"Error fetching data from Redis: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    decoded_values = []
    for value in values:
        if value is not None:
            decoded_values.append(value.decode('utf-8'))
    
    paginated_values = paginate(decoded_values, page, page_size)
    logger.debug(f"Paginated values: {paginated_values}")
    
    return paginated_values

if __name__ == "__main__":
    import hypercorn.asyncio
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:8080"]
    hypercorn.asyncio.run(app, config)
