from dotenv import load_dotenv
from mem0 import MemoryClient
import logging
import json
import os

load_dotenv()

mem0=MemoryClient(api_key=os.getenv("MEM0_API_KEY"))

user_name = "Boss"
mem0 = MemoryClient()


def add_memory():
    messages_formatted = [
        {
            "role": "user",
            "content": "I really like coding."
        },
        {
            "role": "assistant",
            "content": "YAAH it's good."
        },
        {
            "role": "user",
            "content": "I think so too."
        },
        {
            "role": "assistant",
            "content": "What is your favorite song by them?"
        }
    ]

    mem0.add(messages_formatted, user_id="Boss")


def get_memory_by_query():

    query = f"What are {user_name}'s preferences?"
    results = mem0.search(
        query=query,
        filters={
            "user_id": user_name
        }
    )

    memories = [
        {
            "memory": r["memory"],
            "updated_at": r.get("updated_at")
        }
        for r in results["results"]
    ]

    memories_str = json.dumps(memories)
    print(f"Memories: {memories_str}")
    return memories_str

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    add_memory()
    get_memory_by_query()