"""
Blackboard MCP Server
---------------------

This module exposes your Redis-backed blackboard as an MCP (Model Context
Protocol) server over stdio. A typical MCP host (an IDE, agent runtime, or
inspector) will spawn this process and communicate via JSON-RPC 2.0 on stdin
and stdout.

MCP concepts used here:
- Tools: callable operations the host can invoke. We expose:
  - post_message(...): append a message to the Redis Stream
  - get_messages(...): read messages from the Redis Stream

Why stdio: MCP standardizes process-to-process communication via stdio or
websocket. Stdio is the simplest for local development, allowing hosts to
spawn the server as a subprocess without managing ports.

This server is intentionally thin and reuses your existing data model (the
same JSON structure persisted in Redis by the FastAPI app). You can run the
FastAPI API and this MCP server side-by-side; both talk to the same Redis.
"""

from __future__ import annotations

# Standard library imports
import asyncio
import json
import os
from typing import Any, Dict, List

# Third-party imports
import redis.asyncio as redis

# MCP SDK imports
from mcp.server.fastmcp import FastMCP


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Keep the same environment variables as the FastAPI app for consistency.
STREAM_KEY: str = os.getenv("REDIS_STREAM_KEY", "blackboard_messages")
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")


# A lazy-initialized Redis client stored at module scope so all tool calls
# reuse the same connection pool.
_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """
    Return a shared asyncio Redis client, creating it on first use.

    MCP does not have a built-in startup hook in this minimal example, so we
    create the client on-demand the first time a tool is invoked.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


# ---------------------------------------------------------------------------
# MCP Server: define tools that wrap the blackboard's core behaviors
# ---------------------------------------------------------------------------
mcp = FastMCP(name="Blackboard MCP")


@mcp.tool(description="Append a structured message to the blackboard stream.")
async def post_message(
    agent_id: str,
    conversation_id: str,
    message_type: str,
    payload: Dict[str, Any],
) -> str:
    """
    MCP Tool: Append a message entry to the Redis Stream.

    Parameters (MCP transforms these type hints into JSON Schema):
    - agent_id: Who sent the message
    - conversation_id: Conversation/thread identifier
    - message_type: e.g. "thought", "tool_input", "final_answer"
    - payload: Arbitrary structured content associated with the message

    Returns a single text content that includes the created stream ID.
    """
    client = await get_redis_client()
    entry = {
        "agent_id": agent_id,
        "conversation_id": conversation_id,
        "message_type": message_type,
        "payload": payload,
    }

    stream_id = await client.xadd(
        STREAM_KEY,
        fields={"data": json.dumps(entry, separators=(",", ":"))},
    )

    return f"ok:{stream_id}"


@mcp.tool(
    description=(
        "Retrieve messages from the blackboard stream as pretty-printed JSON. "
        "Optionally limit the count."
    )
)
async def get_messages(limit: int | None = None) -> str:
    """
    MCP Tool: Read entries from the Redis Stream.

    - limit: Optional maximum number of entries to return (newest first when
             trimming client-side after XRANGE).

    Returns a single text content containing a JSON array of messages, where
    each item is {"id": <redis_stream_id>, "data": <original_message_dict>}.
    """
    client = await get_redis_client()

    # XRANGE returns from oldest to newest. We support an optional COUNT.
    messages = await client.xrange(
        STREAM_KEY,
        min="-",
        max="+",
        count=limit if isinstance(limit, int) and limit > 0 else None,
    )

    formatted: List[Dict[str, Any]] = []
    for stream_id, fields in messages:
        try:
            data_raw = fields.get("data")
            data_obj = json.loads(data_raw) if isinstance(data_raw, str) else None
        except json.JSONDecodeError:
            data_obj = {"_error": "invalid_json", "raw": fields.get("data")}
        formatted.append({"id": stream_id, "data": data_obj})

    text = json.dumps(formatted, indent=2, ensure_ascii=False)
    return text


# ---------------------------------------------------------------------------
# Entry point: stdio server for MCP hosts
# ---------------------------------------------------------------------------
def _main() -> None:
    """
    Start the stdio transport and serve MCP requests until EOF.

    Note: We call the synchronous runner here because the SDK manages its own
    event loop for stdio. Running this inside asyncio.run() would cause
    "Already running asyncio" errors.
    """
    mcp.run(transport="stdio")


if __name__ == "__main__":
    _main()


