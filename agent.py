"""
This script acts as a "writer" agent. Its job is to send a structured
message to the Blackboard API server. It demonstrates how a real AI agent
would post information to the central log.
"""

# --- Imports ---
import sys
import asyncio
import uuid
import httpx         # A modern, asynchronous HTTP client for making web requests.
import argparse      # A standard library for parsing command-line arguments.

# --- Configuration ---
# The URL of the Blackboard API server's endpoint for posting messages.
API_URL = "http://localhost:8000/message"


# --- Core Function ---
async def send_message(agent_id: str, conversation_id: str, message_type: str, payload: dict) -> None:
    """
    Sends a structured message to the blackboard API.
    """
    # httpx.AsyncClient allows us to send web requests efficiently.
    # The 'async with' block ensures the connection is properly closed.
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            # Send an HTTP POST request to the API server.
            # The 'json' parameter automatically converts our Python dict to a JSON payload.
            resp = await client.post(
                API_URL,
                json={
                    "agent_id": agent_id,
                    "conversation_id": conversation_id,
                    "message_type": message_type,
                    "payload": payload,
                },
            )
            # This will raise an error if the server responded with a failure (e.g., 404, 500).
            resp.raise_for_status()
            # Print the server's response so we know it worked.
            print("Server response:", resp.json())
        except httpx.RequestError as exc:
            # Handle cases where we can't connect to the server at all.
            print(f"Error connecting to the Blackboard API: {exc}")
            print("Is the server running?")


# --- Main Execution Block ---
def main() -> None:
    """
    This is the main function that runs when the script is executed.
    It handles parsing command-line arguments and calling the send_message function.
    """
    # Set up the command-line argument parser.
    # This allows users to customize the message from the command line.
    parser = argparse.ArgumentParser(description="Send a structured message to the Blackboard.")
    parser.add_argument("--agent-id", default=f"agent-{uuid.uuid4()}", help="The ID of the agent.")
    parser.add_argument("--conversation-id", default=f"conv-{uuid.uuid4()}", help="The ID of the conversation.")
    parser.add_argument("message", help="A simple message string, which will be put into the payload.")
    
    # Parse the arguments provided by the user.
    args = parser.parse_args()

    # In a real system, the payload would be more meaningful.
    # Here, we simulate a richer payload based on the simple text message.
    payload = {
        "text": args.message,
        "token_count": len(args.message.split()),
        "some_metric": round(uuid.uuid4().int / 1e35, 2) # A random metric for fun
    }

    print(f"Sending message from '{args.agent_id}'...")
    
    # asyncio.run() starts the asynchronous operation.
    # We call our send_message function with the structured data.
    asyncio.run(
        send_message(
            agent_id=args.agent_id,
            conversation_id=args.conversation_id,
            message_type="thought", # We hardcode this for the demo.
            payload=payload,
        )
    )

# This is a standard Python construct. The code inside this block
# will only run when the script is executed directly (e.g., `python agent.py`).
if __name__ == "__main__":
    main()
