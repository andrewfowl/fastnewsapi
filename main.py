from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
from urllib.parse import urlparse
import os

# Parse Redis URL from environment variable
redis_url = os.getenv('REDIS_URL')
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

# Pydantic model for request body
class Item(BaseModel):
    key: str
    value: str

@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}

@app.post("/set")
async def set_item(item: Item):
    try:
        redis_client.set(item.key, item.value)
        return {"status": "success", "message": f"Key '{item.key}' set successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get/{key}")
async def get_item(key: str):
    try:
        value = redis_client.get(key)
        if value is None:
            raise HTTPException(status_code=404, detail="Key not found")
        return {"status": "success", "key": key, "value": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
