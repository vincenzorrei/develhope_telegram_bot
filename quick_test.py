"""
Quick Test - Verifica che tutti i componenti si inizializzino correttamente
(senza necessità di chiavi API reali per questa fase)
"""

import sys

print("\n" + "="*60)
print("QUICK TEST - Verifica Componenti")
print("="*60 + "\n")

try:
    # Test 1: Import config
    print("[1/6] Testing config.py...")
    import config
    print("      [OK] Config importato")
    print(f"      - Bot name: {config.bot_config.BOT_NAME}")
    print(f"      - LLM model: {config.llm_config.MODEL}")

    # Test 2: Import prompts
    print("\n[2/6] Testing prompts.py...")
    import prompts
    print("      [OK] Prompts importati")
    print(f"      - System prompt: {len(prompts.prompts.SYSTEM_PROMPT)} caratteri")

    # Test 3: Import vector store (senza inizializzare ChromaDB)
    print("\n[3/6] Testing vector_store.py...")
    from src.rag.vector_store import VectorStoreManager
    print("      [OK] VectorStoreManager class caricata")

    # Test 4: Import document processor
    print("\n[4/6] Testing document_processor.py...")
    from src.rag.document_processor import DocumentProcessor
    print("      [OK] DocumentProcessor class caricata")

    # Test 5: Import bot engine (senza inizializzare - richiede OpenAI key)
    print("\n[5/6] Testing bot_engine.py...")
    from bot_engine import LangChainEngine
    print("      [OK] LangChainEngine class caricata")

    # Test 6: Import telegram components
    print("\n[6/6] Testing telegram components...")
    from src.telegram.handlers import setup_handlers
    from src.telegram.bot_setup import create_bot
    from src.telegram.message_processor import MessageProcessor
    print("      [OK] Telegram components caricati")

    print("\n" + "="*60)
    print("[SUCCESS] Tutti i componenti si importano correttamente!")
    print("="*60)
    print("\n[NEXT STEP] Configura le API keys reali in .env per test completo")

except Exception as e:
    print(f"\n[ERROR] Test fallito: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
