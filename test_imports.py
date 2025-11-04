"""
Test script per verificare che tutti i moduli si importino correttamente.
"""

print("\n" + "="*60)
print("TEST IMPORTS - Verifica dipendenze")
print("="*60 + "\n")

import sys

def test_import(module_name, description):
    """Test import di un modulo."""
    try:
        __import__(module_name)
        print(f"[OK] {description:40} - {module_name}")
        return True
    except ImportError as e:
        print(f"[ERROR] {description:40} - {e}")
        return False
    except Exception as e:
        print(f"[WARN] {description:40} - {type(e).__name__}: {e}")
        return False

# Counter
success = 0
total = 0

# Test core dependencies
print("\n[1/5] Testing Core Dependencies...")
print("-" * 60)
tests = [
    ("telegram", "python-telegram-bot"),
    ("telegram.ext", "telegram.ext"),
    ("openai", "OpenAI"),
    ("dotenv", "python-dotenv"),
]
for module, desc in tests:
    total += 1
    if test_import(module, desc):
        success += 1

# Test LangChain
print("\n[2/5] Testing LangChain...")
print("-" * 60)
tests = [
    ("langchain", "LangChain core"),
    ("langchain_core", "LangChain core (new)"),
    ("langchain_community", "LangChain community"),
    ("langchain_openai", "LangChain OpenAI"),
    ("langchain_text_splitters", "LangChain text splitters"),
]
for module, desc in tests:
    total += 1
    if test_import(module, desc):
        success += 1

# Test ChromaDB
print("\n[3/5] Testing ChromaDB...")
print("-" * 60)
tests = [
    ("chromadb", "ChromaDB"),
    ("hnswlib", "HNSW lib (via chroma-hnswlib)"),
]
for module, desc in tests:
    total += 1
    if test_import(module, desc):
        success += 1

# Test document processors
print("\n[4/5] Testing Document Processors...")
print("-" * 60)
tests = [
    ("pypdf", "PyPDF (PDF loader)"),
    ("docx", "python-docx (DOCX loader)"),
]
for module, desc in tests:
    total += 1
    if test_import(module, desc):
        success += 1

# Test project modules
print("\n[5/5] Testing Project Modules...")
print("-" * 60)
tests = [
    ("config", "config.py"),
    ("prompts", "prompts.py"),
    ("bot_engine", "bot_engine.py"),
]
for module, desc in tests:
    total += 1
    if test_import(module, desc):
        success += 1

# Summary
print("\n" + "="*60)
print(f"RISULTATO: {success}/{total} moduli importati correttamente")
print("="*60)

if success == total:
    print("\n[SUCCESS] Tutti i moduli funzionano! Ready to run.")
    sys.exit(0)
else:
    print(f"\n[WARNING] {total - success} moduli hanno problemi.")
    sys.exit(1)
