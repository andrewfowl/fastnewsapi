from fastapi import FastAPI, Depends, Query, HTTPException
from redis_client import init_redis_pool, close_redis_pool, redis
from pagination import paginate
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(on_startup=[init_redis_pool], on_shutdown=[close_redis_pool])

async def get_redis():
    return redis

@app.get("/rss", response_model=List[str])
async def get_data(
    keys: List[str] = Query(..., description="List of Redis keys to retrieve"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    redis=Depends(get_redis)
):
    pipe = redis.pipeline()
    for key in keys:
        pipe.get(key)
    try:
        values = await pipe.execute()
    except Exception as e:
        logger.error(f"Error fetching data from Redis: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    decoded_values = [value.decode('utf-8') for value in values if value]
    paginated_values = paginate(decoded_values, page, page_size)
    logger.debug(f"Paginated values: {paginated_values}")
    
    return paginated_values


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
