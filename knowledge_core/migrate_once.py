"""
migrate_once.py
Run this ONE TIME to move all your old knowledge_db.json into ChromaDB.
Delete this file after running.
"""

from knowledge_core.chroma_manager import get_chroma_manager

def run_migration():
    print("[Migration] Starting...")
    chroma = get_chroma_manager()
    count  = chroma.migrate_from_json()
    print(f"[Migration] Done! {count} entries moved to ChromaDB.")
    print(f"[Migration] Total in ChromaDB: {chroma.count()}")

if __name__ == "__main__":
    run_migration()