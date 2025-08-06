"""
This script acts as a "reader" agent. Its job is to retrieve and display
all the messages that have been logged to the Blackboard. It demonstrates
how a monitoring tool or another agent would consume information from
the central log.
"""

# --- Imports ---
import httpx     # The HTTP client for making web requests.
import asyncio   # For running the asynchronous code.
import json      # For parsing the JSON data stored in Redis.

# --- Configuration ---
# The URL of the Blackboard API server's endpoint for retrieving messages.
API_URL = "http://localhost:8000/messages"


# --- Core Function ---
async def read_messages() -> None:
    """
    Connects to the API, fetches all messages, and prints them.
    """
    # httpx.AsyncClient allows us to send web requests efficiently.
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Send an HTTP GET request to the API server to get the messages.
            resp = await client.get(API_URL)
            # Raise an error if the server responded with a failure (e.g., 404, 500).
            resp.raise_for_status()
            # Parse the JSON response from the server into a Python dictionary.
            data = resp.json()
            
            print("--- Blackboard Messages ---")
            
            # Check if the 'messages' list is empty.
            if not data.get("messages"):
                print("The blackboard is empty.")
            else:
                # Loop through each message returned by the API.
                # The API returns a list of tuples, where each tuple contains
                # the unique message ID and a dictionary of its fields.
                for msg_id, fields in data["messages"]:
                    # The actual message content is a JSON string in the 'data' field.
                    # We need to parse this string to get the structured data.
                    message_data = json.loads(fields['data'])
                    
                    # Extract the details from the parsed message data.
                    # .get() is used to avoid errors if a key is missing.
                    agent_id = message_data.get('agent_id', 'N/A')
                    convo_id = message_data.get('conversation_id', 'N/A')
                    msg_type = message_data.get('message_type', 'N/A')
                    payload = message_data.get('payload', {})
                    
                    # Print the message details in a readable format.
                    print(f"ID: {msg_id} | Agent: {agent_id} | Conversation: {convo_id}")
                    print(f"  Type: {msg_type}")
                    print(f"  Payload: {payload}")
                    print("-" * 20)

        except httpx.RequestError as exc:
            # Handle cases where we can't connect to the server.
            print(f"Error connecting to the Blackboard API: {exc}")
            print("Is the server running? (uvicorn blackboard.main:app --reload)")
        except Exception as exc:
            # Catch any other unexpected errors during the process.
            print(f"An unexpected error occurred: {exc}")


# --- Main Execution Block ---
def main() -> None:
    """The main function that runs when the script is executed."""
    # asyncio.run() starts the asynchronous read_messages function.
    asyncio.run(read_messages())


# This is a standard Python construct. The code inside this block
# will only run when the script is executed directly (e.g., `python reader.py`).
if __name__ == "__main__":
    main()
