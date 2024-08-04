import os
import asyncio
import redis.asyncio as redis
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, Query, HTTPException
from contextlib import asynccontextmanager
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import ConnectionError, DataError, NoScriptError, RedisError, ResponseError
from redis.commands.search.query import Query as rQuery
from typing import List, Dict
import logging

redis_url = os.getenv("REDIS_URL")
redis_port = int(os.getenv("REDISPORT", 6379))
redis_host = os.getenv("REDISHOST")
redis_pass = os.getenv("REDIS_PASSWORD")

logging.basicConfig(level=logging.INFO)

class RedisManager:
    redis_client: redis.Redis = None

    @classmethod
    async def connect(
        cls, host: str = redis_host, port: int = redis_port, username: str = "default", password=redis_pass
    ):
        try:
            cls.redis_client = redis.StrictRedis(
                host=host, port=port, username=username, password=password, decode_responses=True
            )
            logging.info("Connected to Redis")
            test_ping = await cls.redis_client.ping()  # Test connection
            logging.info(f"Successfull ping: {test_ping}")
        except redis.RedisError as e:
            logging.error(f"Failed to connect to Redis: {e}")
            raise

    @classmethod
    async def close(cls):
        if cls.redis_client is not None:
            await cls.redis_client.close()
            logging.info("Redis connection closed")

    @classmethod
    async def query_rss_feed(cls, start: int, end: int) -> List[Dict[str, str]]:
        try:
            feed_ids = await cls.redis_client.zrevrange('rss_feed', start, end)
            logging.info(f"Retrieved feed_ids: {feed_ids}")
            tasks = [cls.redis_client.hgetall(f'rss_feed_item:{feed_id}') for feed_id in feed_ids]
            feed_items = await asyncio.gather(*tasks)
            logging.info(f"Retrieved feed_items: {feed_items}")
            return feed_items
        except redis.RedisError as e:
            logging.error(f"Failed to query RSS feed from Redis: {e}")
            raise

async def run_redis():
    await RedisManager.connect()
    logging.info("run_redis >> RedisManager.connect() status: success")
    return RedisManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting application lifespan")
    logging.info(isinstance(app.state,State))
    app.state.redis_manager = await run_redis()
    yield
    logging.info("Ending application lifespan")
    await RedisManager.close()
    logging.info("Closed RedisManager and ended lifespan")

app = FastAPI(lifespan=lifespan)

@app.get("/rss", response_model=List[Dict[str, str]])
async def get_rss(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    redis_manager: RedisManager = request.app.state.redis_manager
    start = (page - 1) * page_size
    end = start + page_size - 1
    try:
        feed_items = await redis_manager.query_rss_feed(start, end)
        
        return JSONResponse({"data": feed_items, "dt": datetime.now().isoformat()})
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import hypercorn
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:8080"]
    asyncio.run(hypercorn.asyncio.serve(app, config))
