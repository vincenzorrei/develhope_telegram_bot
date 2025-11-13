"""
Script per ricaricare automaticamente i documenti nel vector store.

Usa questo script dopo aver ricreato il vector store.
"""

import sys
import os
from pathlib import Path

# Setup workaround SQLite se necessario
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    print("[SETUP] Using pysqlite3")
except ImportError:
    print("[SETUP] Using system sqlite3")

from src.rag.vector_store import VectorStoreManager
from src.rag.document_processor import DocumentProcessor

def reload_all_documents():
    """Ricarica tutti i documenti da data/documents/"""

    print("\n" + "="*60)
    print("RELOAD DOCUMENTS - Auto-reload script")
    print("="*60)

    # Inizializza componenti
    print("\n[1/3] Initializing components...")
    vector_store = VectorStoreManager()
    document_processor = DocumentProcessor()

    # Trova documenti
    docs_dir = Path("./data/documents")
    if not docs_dir.exists():
        print(f"\n❌ ERROR: Documents directory not found: {docs_dir}")
        return False

    doc_files = list(docs_dir.glob("doc_*.*"))

    if not doc_files:
        print(f"\n⚠️  WARNING: No documents found in {docs_dir}")
        return False

    print(f"   Found {len(doc_files)} documents")

    # Carica ogni documento
    print(f"\n[2/3] Loading {len(doc_files)} documents...")

    success_count = 0
    failed_count = 0

    for i, doc_file in enumerate(doc_files, 1):
        filename = doc_file.name
        filepath = str(doc_file)

        print(f"\n   [{i}/{len(doc_files)}] Processing: {filename}")

        try:
            doc_id, num_chunks, summary = document_processor.process_and_add(
                filepath=filepath,
                filename=filename,
                vector_store=vector_store
            )

            print(f"   ✅ SUCCESS:")
            print(f"      - Doc ID: {doc_id}")
            print(f"      - Chunks: {num_chunks}")
            print(f"      - Summary: {summary[:80]}...")

            success_count += 1

        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            failed_count += 1

    # Summary
    print("\n" + "="*60)
    print("[3/3] SUMMARY")
    print("="*60)
    print(f"   Total documents: {len(doc_files)}")
    print(f"   ✅ Loaded successfully: {success_count}")
    print(f"   ❌ Failed: {failed_count}")

    # Stats finali
    stats = vector_store.get_stats()
    print(f"\n   Vector Store Stats:")
    print(f"   - Total chunks: {stats['total_chunks']}")
    print(f"   - Total documents: {stats['total_documents']}")
    print("="*60)

    return failed_count == 0

if __name__ == "__main__":
    success = reload_all_documents()
    sys.exit(0 if success else 1)
