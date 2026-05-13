try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except Exception:
    load_dotenv = None
    _HAS_DOTENV = False

if _HAS_DOTENV:
    load_dotenv()

try:
    from mem0 import MemoryClient as _Mem0Client
    _HAS_MEM0 = True
except Exception:
    _Mem0Client = None
    _HAS_MEM0 = False
import logging
import json
import os

class MemoryClient:
    def __init__(self, *args, **kwargs):
        self._client = _Mem0Client(*args, **kwargs) if _HAS_MEM0 else None

    def add(self, *args, **kwargs):
        if self._client is None:
            print("[Memory] mem0 not available; skipping add.")
            return None
        return self._client.add(*args, **kwargs)

    def search(self, *args, **kwargs):
        if self._client is None:
            print("[Memory] mem0 not available; skipping search.")
            return {"results": []}
        return self._client.search(*args, **kwargs)


mem0 = MemoryClient(api_key=os.getenv("MEM0_API_KEY")) if _HAS_MEM0 else MemoryClient()

user_name = "Boss"


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
