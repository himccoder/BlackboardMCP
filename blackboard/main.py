"""Blackboard MCP FastAPI application.
Receives messages from agents and logs them to Redis Streams.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import redis.asyncio as redis

STREAM_KEY = os.getenv("REDIS_STREAM_KEY", "blackboard_messages")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

app = FastAPI(title="Blackboard MCP", version="0.1.0")

class Message(BaseModel):
    agent_id: str
    conversation_id: str
    message_type: str  # e.g., "thought", "tool_input", "final_answer"
    payload: dict  # Flexible content like {"prompt": "...", "result": "..."}

@app.on_event("startup")
async def startup() -> None:
    """Create a Redis connection on application startup."""
    app.state.redis = redis.from_url(REDIS_URL, decode_responses=True)

@app.on_event("shutdown")
async def shutdown() -> None:
    """Close Redis connection on application shutdown."""
    redis_client = app.state.redis
    if redis_client:
        await redis_client.close()

@app.post("/message")
async def post_message(message: Message):
    """Receive a message from an agent and append it to the Redis stream."""
    try:
        stream_id = await app.state.redis.xadd(
            STREAM_KEY,
            fields={
                # Pydantic v2 .model_dump() is preferred
                "data": message.model_dump_json()
            },
        )
        return {"status": "ok", "id": stream_id}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/messages")
async def get_messages():
    """Retrieve all messages from the Redis stream."""
    try:
        # XRANGE gets all messages from the beginning ('-') to the end ('+')
        messages = await app.state.redis.xrange(STREAM_KEY, min="-", max="+")
        return {"status": "ok", "messages": messages}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc
