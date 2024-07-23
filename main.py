from fastapi import FastAPI, HTTPException, Depends
from redis_client import init_redis_pool, close_redis_pool, redis
from typing import List

app = FastAPI(on_startup=[init_redis_pool], on_shutdown=[close_redis_pool])

async def get_redis():
    return redis

@app.get("/rss", response_model=List[str])
async def get_data(keys: List[str], redis=Depends(get_redis)):
    try:
        pipe = redis.pipeline()
        for key in keys:
            pipe.get(key)
        values = await pipe.execute()
        return [value.decode('utf-8') for value in values if value]
    except Exception as e:
        print(f"Error fetching items from Redis: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch items from Redis")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
