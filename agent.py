"""Demo agent that sends a richly structured message to the Blackboard MCP."""

import sys
import asyncio
import uuid
import httpx
import argparse

API_URL = "http://localhost:8000/message"

async def send_message(agent_id: str, conversation_id: str, message_type: str, payload: dict) -> None:
    """Sends a structured message to the blackboard."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.post(
                API_URL,
                json={
                    "agent_id": agent_id,
                    "conversation_id": conversation_id,
                    "message_type": message_type,
                    "payload": payload,
                },
            )
            resp.raise_for_status()
            print("Server response:", resp.json())
        except httpx.RequestError as exc:
            print(f"Error connecting to the Blackboard API: {exc}")
            print("Is the server running?")


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a structured message to the Blackboard.")
    parser.add_argument("--agent-id", default=f"agent-{uuid.uuid4()}", help="The ID of the agent.")
    parser.add_argument("--conversation-id", default=f"conv-{uuid.uuid4()}", help="The ID of the conversation.")
    parser.add_argument("message", help="A simple message string, which will be put into the payload.")
    
    args = parser.parse_args()

    # Simulate a more complex payload based on the message
    payload = {
        "text": args.message,
        "token_count": len(args.message.split()),
        "some_metric": round(uuid.uuid4().int / 1e35, 2) # A random metric for fun
    }

    print(f"Sending message from '{args.agent_id}'...")
    asyncio.run(
        send_message(
            agent_id=args.agent_id,
            conversation_id=args.conversation_id,
            message_type="thought",
            payload=payload,
        )
    )

if __name__ == "__main__":
    main()
