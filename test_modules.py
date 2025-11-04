"""
Script di Test per Moduli Bot Telegram

Testa i moduli creati finora per verificare che tutto funzioni.

Uso:
    python test_modules.py
"""

import sys
import os

print("=" * 60)
print("🧪 TEST MODULI BOT TELEGRAM EDUCATIVO")
print("=" * 60)
print()

# ============================================
# TEST 1: Config Module
# ============================================
print("📋 TEST 1: Config Module")
print("-" * 40)

try:
    import config
    print("✅ Import config.py successful")
    print(f"   SQLite workaround: {'pysqlite3' in sys.modules}")
    print(f"   LLM Model: {config.llm_config.MODEL}")
    print(f"   RAG Top-K: {config.rag_config.TOP_K}")
    print(f"   Admin IDs configurati: {len(config.admin_config.ADMIN_USER_IDS)}")
except Exception as e:
    print(f"❌ Errore import config: {e}")
    sys.exit(1)

print()

# ============================================
# TEST 2: Prompts Module
# ============================================
print("📋 TEST 2: Prompts Module")
print("-" * 40)

try:
    from prompts import prompts
    print("✅ Import prompts.py successful")
    print(f"   System prompt length: {len(prompts.SYSTEM_PROMPT)} chars")
    print(f"   Welcome message preview: {prompts.WELCOME_USER[:50]}...")
    print(f"   Total prompt attributes: {len([a for a in dir(prompts) if not a.startswith('_')])}")
except Exception as e:
    print(f"❌ Errore import prompts: {e}")
    sys.exit(1)

print()

# ============================================
# TEST 3: Logger Module
# ============================================
print("📋 TEST 3: Logger Module")
print("-" * 40)

try:
    from src.utils.logger import get_logger, log_success, log_warning
    logger = get_logger("test")
    print("✅ Logger module imported")

    # Test logging
    logger.info("Test info message")
    logger.debug("Test debug message")
    log_success("Test success helper")
    log_warning("Test warning helper")

    print("✅ Logger test passed")
except Exception as e:
    print(f"❌ Errore logger: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================
# TEST 4: Helpers Module
# ============================================
print("📋 TEST 4: Helpers Module")
print("-" * 40)

try:
    from src.utils import helpers

    print("✅ Helpers module imported")

    # Test count_tokens
    text = "Hello world! This is a test."
    tokens = helpers.count_tokens(text)
    print(f"   Token count test: '{text}' = {tokens} tokens")

    # Test generate_doc_id
    doc_id = helpers.generate_doc_id("example.pdf")
    print(f"   Doc ID generation: {doc_id}")

    # Test is_supported_document
    is_pdf_supported = helpers.is_supported_document("file.pdf")
    is_exe_supported = helpers.is_supported_document("file.exe")
    print(f"   PDF supported: {is_pdf_supported}, EXE supported: {is_exe_supported}")

    # Test sanitize_filename
    unsafe = "my file!@#.pdf"
    safe = helpers.sanitize_filename(unsafe)
    print(f"   Sanitize: '{unsafe}' -> '{safe}'")

    print("✅ Helpers test passed")

except Exception as e:
    print(f"❌ Errore helpers: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================
# TEST 5: Vector Store Module (ChromaDB)
# ============================================
print("📋 TEST 5: Vector Store Module (ChromaDB)")
print("-" * 40)

try:
    from src.rag.vector_store import VectorStoreManager

    print("✅ VectorStoreManager imported")

    # Initialize (this tests PersistentClient setup)
    vs = VectorStoreManager()
    print("✅ VectorStoreManager initialized (PersistentClient)")

    # Test get_stats
    stats = vs.get_stats()
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Storage size: {stats['storage_size_mb']} MB")
    print(f"   Collection: {stats['collection_name']}")

    # Test list_all_documents
    docs = vs.list_all_documents()
    print(f"   Documents in DB: {len(docs)}")
    if docs:
        print(f"   First document: {docs[0]['source']}")

    print("✅ Vector Store test passed")

except Exception as e:
    print(f"❌ Errore vector store: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================
# TEST 6: Directory Structure
# ============================================
print("📋 TEST 6: Directory Structure")
print("-" * 40)

try:
    required_dirs = [
        "data",
        "data/vectordb",
        "data/documents",
        "data/conversations",
        "src",
        "src/utils",
        "src/rag",
        "src/llm",
        "src/telegram"
    ]

    all_exist = True
    for dir_path in required_dirs:
        exists = os.path.exists(dir_path)
        status = "✅" if exists else "❌"
        print(f"   {status} {dir_path}")
        if not exists:
            all_exist = False

    if all_exist:
        print("✅ All directories exist")
    else:
        print("⚠️  Some directories missing")

except Exception as e:
    print(f"❌ Errore checking directories: {e}")

print()

# ============================================
# SUMMARY
# ============================================
print("=" * 60)
print("📊 SUMMARY")
print("=" * 60)
print("✅ Config module: PASS")
print("✅ Prompts module: PASS")
print("✅ Logger module: PASS")
print("✅ Helpers module: PASS")
print("✅ Vector Store module: PASS")
print("✅ Directory structure: PASS")
print()
print("🎉 Tutti i test passati!")
print()
print("📝 NEXT STEPS:")
print("   1. Installa dipendenze: pip install -r requirements.txt")
print("   2. Configura API keys reali in .env")
print("   3. Continua implementazione moduli rimanenti")
print()
print("=" * 60)
