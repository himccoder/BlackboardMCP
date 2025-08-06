"""
This file defines the main web server for the Blackboard system.
It uses the FastAPI framework to create API endpoints that agents can
interact with. Its primary job is to receive messages and log them
to a Redis database.
"""

# --- Imports ---
# Import necessary libraries and classes.
from fastapi import FastAPI, HTTPException  # FastAPI is the web framework. HTTPException is for sending errors.
from pydantic import BaseModel             # Pydantic is used for data validation and modeling.
import os                                  # Used to get configuration from environment variables.
import redis.asyncio as redis              # The asynchronous Redis client library for database interaction.


# --- Configuration ---
# Define configuration variables. Using environment variables is good practice.
# This is the name of the key in Redis where messages will be stored.
STREAM_KEY = os.getenv("REDIS_STREAM_KEY", "blackboard_messages")
# The connection URL for the Redis database. Defaults to a local instance.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


# --- FastAPI Application ---
# Create an instance of the FastAPI application. This is our main web server object.
app = FastAPI(
    title="Blackboard MCP",
    description="A centralized message logger for multi-agent systems.",
    version="0.1.0"
)


# --- Data Model ---
# Define the structure of an incoming message using Pydantic.
# This ensures that any data sent to the '/message' endpoint is valid.
class Message(BaseModel):
    """Represents a single message logged by an agent."""
    agent_id: str
    conversation_id: str
    message_type: str  # e.g., "thought", "tool_input", "final_answer"
    payload: dict      # Flexible content like {"prompt": "...", "result": "..."}


# --- Redis Connection Management ---
# These functions handle the connection to the Redis database.

@app.on_event("startup")
async def startup() -> None:
    """This function runs when the server starts up."""
    # Create a connection to the Redis database and store it in the app's state.
    # This connection pool will be reused for all requests, which is efficient.
    app.state.redis = redis.from_url(REDIS_URL, decode_responses=True)

@app.on_event("shutdown")
async def shutdown() -> None:
    """This function runs when the server is shutting down."""
    # Gracefully close the connection to the Redis database.
    redis_client = app.state.redis
    if redis_client:
        await redis_client.close()


# --- API Endpoints ---
# These are the functions that handle requests from agents.

@app.post("/message")
async def post_message(message: Message):
    """
    Receives a message from an agent and appends it to the Redis stream.
    This endpoint handles HTTP POST requests to the '/message' URL.
    """
    try:
        # The 'xadd' command appends a new entry to a Redis Stream.
        # We store the entire message as a single JSON string in a field called 'data'.
        stream_id = await app.state.redis.xadd(
            STREAM_KEY,
            fields={"data": message.model_dump_json()}
        )
        # If successful, return a confirmation and the unique ID of the new message.
        return {"status": "ok", "id": stream_id}
    except Exception as exc:
        # If anything goes wrong with the database operation, send an error.
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/messages")
async def get_messages():
    """
    Retrieves all messages from the Redis stream.
    This endpoint handles HTTP GET requests to the '/messages' URL.
    """
    try:
        # The 'xrange' command gets items from a stream within a given range.
        # Here, '-' means the very beginning and '+' means the very end, so we get all messages.
        messages = await app.state.redis.xrange(STREAM_KEY, min="-", max="+")
        # Return the list of messages.
        return {"status": "ok", "messages": messages}
    except Exception as exc:
        # If anything goes wrong, send an error.
        raise HTTPException(status_code=500, detail=str(exc)) from exc
