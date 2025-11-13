"""
Test script per verificare History-Aware RAG implementation.

IMPORTANTE: Questo script testa solo l'inizializzazione,
non avvia il bot Telegram.
"""

import sys
import asyncio

# Setup workaround SQLite se necessario
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    print("[SETUP] Using pysqlite3")
except ImportError:
    print("[SETUP] Using system sqlite3")

from src.rag.vector_store import VectorStoreManager
from bot_engine import LangChainEngine

async def test_initialization():
    """Test che l'engine si inizializzi correttamente con history-aware RAG."""
    print("\n" + "="*60)
    print("TEST: History-Aware RAG Initialization")
    print("="*60)

    try:
        # 1. Inizializza vector store
        print("\n[1/3] Initializing vector store...")
        vector_store = VectorStoreManager()
        print(f"      Documents: {len(vector_store.list_all_documents())}")

        # 2. Inizializza LangChain Engine (include RAG chain)
        print("\n[2/3] Initializing LangChain Engine...")
        engine = LangChainEngine(vector_store)

        # 3. Verifica che la RAG chain esista
        print("\n[3/3] Verifying history-aware RAG chain...")
        assert hasattr(engine, 'rag_chain'), "RAG chain not found!"
        print("      rag_chain: OK")

        # Test componenti chain
        print("\n[COMPONENTS CHECK]")
        print(f"  - LLM: {engine.llm.model_name}")
        print(f"  - Retriever: {type(engine.retriever).__name__}")
        print(f"  - RAG Chain: {type(engine.rag_chain).__name__}")
        print(f"  - Agent Executor: {type(engine.agent_executor).__name__}")
        print(f"  - Memory Manager: {type(engine.memory_manager).__name__}")

        print("\n" + "="*60)
        print("SUCCESS: All components initialized correctly!")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n[ERROR] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_simple_query():
    """Test semplice con una query (se ci sono documenti)."""
    print("\n" + "="*60)
    print("TEST: Simple Query (if documents available)")
    print("="*60)

    try:
        # Setup
        vector_store = VectorStoreManager()
        docs = vector_store.list_all_documents()

        if not docs:
            print("\n[SKIP] No documents in vector store, skipping query test")
            return True

        print(f"\n[INFO] Found {len(docs)} documents")

        engine = LangChainEngine(vector_store)

        # Test query semplice
        test_query = "Ciao, come va?"
        print(f"\n[TEST] Query: '{test_query}'")
        print("[PROCESSING] ...")

        response = await engine.process_message(test_query, user_id=999999)

        print(f"\n[RESPONSE] ({len(response)} chars)")
        print(f"{response[:200]}...")

        print("\n" + "="*60)
        print("SUCCESS: Query processed successfully!")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n[ERROR] Query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n")
    print("█" * 60)
    print("  HISTORY-AWARE RAG - TEST SUITE")
    print("█" * 60)

    # Test 1: Initialization
    result1 = asyncio.run(test_initialization())

    # Test 2: Simple query (opzionale)
    if result1:
        result2 = asyncio.run(test_simple_query())
    else:
        result2 = False

    # Summary
    print("\n")
    print("█" * 60)
    print("  TEST SUMMARY")
    print("█" * 60)
    print(f"  Initialization: {'PASS' if result1 else 'FAIL'}")
    print(f"  Simple Query:   {'PASS' if result2 else 'FAIL'}")
    print("█" * 60)

    # Exit code
    sys.exit(0 if (result1 and result2) else 1)
