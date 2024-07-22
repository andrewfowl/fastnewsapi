from fastapi import FastAPI, HTTPException
import redis
from urllib.parse import urlparse
import os

# Parse Redis URL from environment variable
redis_url = os.getenv('REDIS_PRIVATE_URL', os.getenv('REDIS_URL'))
parsed_url = urlparse(redis_url)

# Connect to Redis
redis_client = redis.StrictRedis(
    host=parsed_url.hostname,
    port=parsed_url.port,
    password=parsed_url.password,
    decode_responses=True
)

# Initialize FastAPI app
app = FastAPI()

# Validate Redis connection
def validate_redis_connection():
    try:
        redis_client.ping()
        print("Connected to Redis successfully")
    except redis.ConnectionError as e:
        print(f"Error connecting to Redis: {e}")
        raise HTTPException(status_code=500, detail="Could not connect to Redis")

# Validate connection at startup
validate_redis_connection()

@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}

@app.get("/rss")
async def get_all_items():
    try:
        keys = redis_client.keys()
        items = []
        for key in keys:
            value = redis_client.get(key)
            items.append({"key": key, "value": value})
        return items
    except Exception as e:
        print(f"Error fetching items from Redis: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch items from Redis")
