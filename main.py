import os
import asyncio
import redis.asyncio as redis
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi.datastructures import State
from fastapi import FastAPI, Request, Query, HTTPException
from contextlib import asynccontextmanager
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import ConnectionError, DataError, NoScriptError, RedisError, ResponseError
from redis.commands.search.query import Query as rQuery
from typing import List, Dict, Any
import logging
import json
from pydantic import BaseModel

redis_url = os.getenv("REDIS_URL")
redis_port = int(os.getenv("REDISPORT", 6379))
redis_host = os.getenv("REDISHOST")
redis_pass = os.getenv("REDIS_PASSWORD")

logging.basicConfig(level=logging.INFO)

class Item(BaseModel):
    published: datetime | None = None
    link: str | None = None
    title: str | None = None
    summary: str | None = None

class ModelOut(BaseModel):
    data: List[Item]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    dt: str

async def get_data(redis_client, key):
    data = {
        "published": await redis_client.hget(key, "published"),
        "link": await redis_client.hget(key, "link"),
        "title": await redis_client.hget(key, "title"),
        "summary": await redis_client.hget(key, "summary")
    }
    return data

#async def get_feed_ids(redis_client, start_index, end_index): 
async def get_feed_ids(redis_client): 
    pattern = "rss_item:*"
    logging.info(f"Fetching keys with pattern: {pattern}")
    keys = await redis_client.keys(pattern)
    logging.info(f"Retrieved keys: {keys}")
    data = [await get_data(redis_client, key) for key in keys]
    logging.info(f"Retrieved data for all keys: {data}")
    data.sort(key=lambda x: datetime.strptime(x['published'], '%Y-%m-%dT%H:%M:%S'))
    logging.info(f"Sorted data: {data}")
    result = data
    logging.info(f"Result data: {result}")
    return result
    
class RedisManager:
    redis_client: redis.Redis = None

    @classmethod
    async def connect(
        cls, host: str = redis_host, port: int = redis_port, username: str = "default", password=redis_pass
    ):
        try:
            cls.redis_client = redis.Redis(host=host, port=port, username=username, password=password, decode_responses=True)
            logging.info("Connected to Redis")
            test_ping = await cls.redis_client.ping()  # Test connection
            if test_ping:
                logging.info("Connected to Redis")
            else:
                logging.error("Not connected to Redis")
        except redis.RedisError as e:
            logging.error(f"Failed to connect to Redis: {e}")
            raise

    @classmethod
    async def close(cls):
        if cls.redis_client is not None:
            await cls.redis_client.close()
            logging.info("Redis connection closed")

    @classmethod
    async def query_rss_feed(cls, start: int, end: int) -> Dict[str, List[Dict[str, str]]]:
        try:
            logging.info(f"Querying RSS feed from {start} to {end}")
            #data = await get_feed_ids(cls.redis_client, start, end)
            data = await get_feed_ids(cls.redis_client)
            total_items = len(data)
            feed_items = data[start:end]
            logging.info(f"Retrieved feed items: {feed_items}")
            return {"total_items": total_items, "items": feed_items}
        except redis.RedisError as e:
            logging.error(f"Failed to query RSS feed from Redis: {e}")
            raise

async def run_redis():
    await RedisManager.connect()
    return RedisManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Start application lifespan")
    logging.info(isinstance(app.state,State))
    app.state.redis_manager = await run_redis()
    yield
    await RedisManager.close()
    logging.info("End application lifespan")

app = FastAPI(lifespan=lifespan)

@app.get("/rss", response_model=ModelOut)
async def get_rss(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    redis_manager: RedisManager = request.app.state.redis_manager
    start = (page - 1) * page_size
    end = start + page_size
    try:
        result = await redis_manager.query_rss_feed(start, end)
        feed_items = result["items"]
        total_items = result["total_items"]
        response = {
            "data": feed_items,
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": (total_items + page_size - 1) // page_size,  # calculate total pages
            "dt": datetime.now().isoformat()
        }
        logging.info(f"Returning feed items: {response}")
        return JSONResponse(response)
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving data")

if __name__ == "__main__":
    import hypercorn
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:8080"]
    asyncio.run(hypercorn.asyncio.serve(app, config))
