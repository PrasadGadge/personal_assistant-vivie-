import json
import os
import threading
import atexit
from concurrent.futures import ThreadPoolExecutor
from memory_core.mem0_client import MemoryClient
from memory_core.Chatcontext import ChatContext

# ✅ NEW — episodic memory import
from memory_core.episodic_memory import store_episode, get_episode_context

mem0    = MemoryClient()
USER_ID = "Boss"
_store_executor = ThreadPoolExecutor(max_workers=1)
atexit.register(_store_executor.shutdown, wait=True)

def retrieve_memory(query: str) -> ChatContext:
    ctx = ChatContext()

    try:
        # ✅ Run mem0 with a timeout — 3 seconds max
        import threading

        result_holder = [None]
        error_holder  = [None]

        def fetch():
            try:
                result_holder[0] = mem0.search(
                    query=query,
                    filters={"user_id": USER_ID}
                )
            except Exception as e:
                error_holder[0] = e

        t = threading.Thread(target=fetch, daemon=True)
        t.start()
        t.join(timeout=3)  # ← max 3 seconds, then skip

        if t.is_alive():
            print("[Memory] Timeout — skipping memory retrieval")
            return ctx  # return empty, don't freeze

        results = result_holder[0]

        if error_holder[0]:
            print(f"[Memory Error] {error_holder[0]}")
            return ctx

        if results and results.get("results"):
            memories   = [r["memory"] for r in results["results"]]
            memory_str = json.dumps(memories)
            ctx.add(
                "system",
                f"Relevant long-term memory about the user: {memory_str}"
            )

        # Episodic context
        episode_ctx = get_episode_context(query)
        if episode_ctx:
            ctx.add("system", episode_ctx)

    except Exception as e:
        print(f"[Memory Error] {e}")

    return ctx


def store_memory(user_input: str, assistant_response: str, intent: str = "general"):
    def _store():
        try:
            # Original mem0 storage — unchanged
            mem0.add(
                [
                    {"role": "user",      "content": user_input},
                    {"role": "assistant", "content": assistant_response}
                ],
                user_id=USER_ID
            )

            # ✅ NEW — also store as episode
            store_episode(
                user_input=user_input,
                vivie_response=assistant_response,
                intent=intent
            )

        except Exception as e:
            print(f"[Memory Store Error] {e}")

    _store_executor.submit(_store)
