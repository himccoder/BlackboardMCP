"""Demo agent that reads all messages from the Blackboard MCP."""

import httpx
import asyncio
import json

API_URL = "http://localhost:8000/messages"

async def read_messages() -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(API_URL)
            resp.raise_for_status()
            data = resp.json()
            
            print("--- Blackboard Messages ---")
            if not data.get("messages"):
                print("The blackboard is empty.")
            else:
                for msg_id, fields in data["messages"]:
                    # The entire message is stored in a 'data' field as a JSON string
                    message_data = json.loads(fields['data'])
                    
                    agent_id = message_data.get('agent_id', 'N/A')
                    convo_id = message_data.get('conversation_id', 'N/A')
                    msg_type = message_data.get('message_type', 'N/A')
                    payload = message_data.get('payload', {})
                    
                    print(f"ID: {msg_id} | Agent: {agent_id} | Conversation: {convo_id}")
                    print(f"  Type: {msg_type}")
                    print(f"  Payload: {payload}")
                    print("-" * 20)

        except httpx.RequestError as exc:
            print(f"Error connecting to the Blackboard API: {exc}")
            print("Is the server running? (uvicorn blackboard.main:app --reload)")
        except Exception as exc:
            print(f"An unexpected error occurred: {exc}")


def main() -> None:
    asyncio.run(read_messages())


if __name__ == "__main__":
    main()
