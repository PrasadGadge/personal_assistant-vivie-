"""
chroma_manager.py — Vivie's Vector Knowledge Brain
Replaces keyword JSON matching with semantic understanding.
"""

import os, json, logging, hashlib
from datetime import datetime
try:
    import chromadb
    from chromadb.utils import embedding_functions
    _HAS_CHROMA = True
except Exception:
    chromadb = None
    embedding_functions = None
    _HAS_CHROMA = False

try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except Exception:
    load_dotenv = None
    _HAS_DOTENV = False

if _HAS_DOTENV:
    load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ChromaManager")

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_PATH  = os.path.join(BASE_DIR, "chroma_db")
JSON_DB_PATH    = os.path.join(BASE_DIR, "knowledge_db.json")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ✅ Force local cache — stop redownloading
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HUGGINGFACE_HUB_VERBOSITY"]        = "error"
os.environ["TRANSFORMERS_OFFLINE"]              = "0"
os.environ["HF_TOKEN"]               = os.getenv("HF_TOKEN", "")
os.environ["TRANSFORMERS_CACHE"]     = os.path.join(BASE_DIR, "model_cache")
os.environ["HF_HOME"]                = os.path.join(BASE_DIR, "model_cache")
os.environ["SENTENCE_TRANSFORMERS_HOME"] = os.path.join(BASE_DIR, "model_cache")
class ChromaManager:

    def __init__(self):
        if not _HAS_CHROMA:
            logger.error("ChromaDB not available. Install it with: pip install chromadb")
            self.client = None
            self.embed_fn = None
            self.collection = None
            return
        try:
            self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
            self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL
            )
            self.collection = self.client.get_or_create_collection(
                name="vivie_knowledge",
                embedding_function=self.embed_fn,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"[ChromaDB] Ready. Entries: {self.collection.count()}")
        except Exception as e:
            logger.error(f"[ChromaDB] Init failed: {e}")
            raise

    def store(self, text: str, metadata: dict = None) -> bool:
        try:
            if self.collection is None:
                return False
            if not text or not text.strip():
                return False

            doc_id   = hashlib.md5(text.encode()).hexdigest()
            existing = self.collection.get(ids=[doc_id])
            if existing["ids"]:
                return True  # already exists

            if metadata is None:
                metadata = {}
            metadata["stored_at"] = datetime.now().isoformat()
            metadata["source"]    = metadata.get("source", "user_interaction")

            self.collection.add(
                documents=[text],
                ids=[doc_id],
                metadatas=[metadata]
            )
            logger.info(f"[ChromaDB] Stored: '{text[:60]}'")
            return True
        except Exception as e:
            logger.error(f"[ChromaDB] Store failed: {e}")
            return False

    def retrieve(self, query: str, top_k: int = 3, threshold: float = 0.4) -> list:
        try:
            if self.collection is None:
                return []
            if not query or not query.strip():
                return []
            total = self.collection.count()
            if total == 0:
                return []

            results   = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, total)
            )
            documents = results.get("documents", [[]])[0]
            distances = results.get("distances",  [[]])[0]

            filtered = []
            for doc, dist in zip(documents, distances):
                similarity = 1 - (dist / 2)
                if similarity >= threshold:
                    filtered.append(doc)
                    logger.info(f"[ChromaDB] Match ({similarity:.2f}): '{doc[:50]}'")
            return filtered
        except Exception as e:
            logger.error(f"[ChromaDB] Retrieve failed: {e}")
            return []

    def retrieve_with_metadata(self, query: str, top_k: int = 3) -> list:
        try:
            if self.collection is None:
                return []
            total = self.collection.count()
            if total == 0:
                return []
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, total),
                include=["documents", "metadatas", "distances"]
            )
            output = []
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                output.append({
                    "text":       doc,
                    "metadata":   meta,
                    "similarity": round(1 - (dist / 2), 3)
                })
            return output
        except Exception as e:
            logger.error(f"[ChromaDB] Retrieve+meta failed: {e}")
            return []

    def count(self) -> int:
        if self.collection is None:
            return 0
        return self.collection.count()

    def migrate_from_json(self) -> int:
        """One-time migration from your old knowledge_db.json"""
        if self.collection is None:
            return 0
        if not os.path.exists(JSON_DB_PATH):
            return 0
        try:
            with open(JSON_DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            entries = []
            if isinstance(data, list):
                entries = data
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str):
                        entries.append({"text": value, "topic": key})
                    elif isinstance(value, list):
                        for item in value:
                            entries.append({"text": str(item), "topic": key})

            count = 0
            for entry in entries:
                text = entry.get("text") or entry.get("content") or str(entry) if isinstance(entry, dict) else entry
                meta = {"source": "json_migration"}
                if text and self.store(str(text), meta):
                    count += 1

            logger.info(f"[Migration] {count} entries moved to ChromaDB.")
            return count
        except Exception as e:
            logger.error(f"[Migration] Failed: {e}")
            return 0


class _NoopChromaManager:
    def store(self, text: str, metadata: dict = None) -> bool:
        return False

    def retrieve(self, query: str, top_k: int = 3, threshold: float = 0.4) -> list:
        return []

    def retrieve_with_metadata(self, query: str, top_k: int = 3) -> list:
        return []

    def count(self) -> int:
        return 0

    def migrate_from_json(self) -> int:
        return 0


# Singleton
_instance = None
_noop_instance = _NoopChromaManager()
def get_chroma_manager() -> ChromaManager:
    if not _HAS_CHROMA:
        return _noop_instance
    global _instance
    if _instance is None:
        _instance = ChromaManager()
    return _instance
