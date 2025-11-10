"""
Script diagnostico per verificare il retrieval del RAG
"""
import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

from src.rag.vector_store import VectorStoreManager
from config import paths_config

print("=" * 60)
print("DIAGNOSTICA RAG - Vector Store")
print("=" * 60)

# Inizializza vector store
vs = VectorStoreManager()

# 1. Lista documenti
print("\n[1] DOCUMENTI NEL DATABASE:")
docs = vs.list_all_documents()
for doc in docs:
    print(f"\n  📄 {doc['source']}")
    print(f"     ID: {doc['doc_id']}")
    print(f"     Chunks: {doc['num_chunks']}")
    print(f"     Data: {doc['timestamp'][:10]}")

# 2. Mostra contenuto chunks del documento appena caricato
print("\n\n[2] CONTENUTO CHUNKS (doc_28d48a7a91ec):")
print("-" * 60)

# Get all chunks per quel documento
results = vs.collection.get(
    where={"doc_id": "doc_28d48a7a91ec"}
)

if results and results['ids']:
    for i, chunk_id in enumerate(results['ids'], 1):
        content = results['documents'][i-1]
        metadata = results['metadatas'][i-1]

        print(f"\n  Chunk {i}/{len(results['ids'])}:")
        print(f"  ID: {chunk_id}")
        print(f"  Page: {metadata.get('page', 'N/A')}")
        print(f"  Content ({len(content)} chars):")
        print(f"  ---")
        print(f"  {content[:300]}...")
        print(f"  ---")
else:
    print("  ⚠️ Nessun chunk trovato per doc_28d48a7a91ec")

# 3. Test similarity search con diverse query
print("\n\n[3] TEST SIMILARITY SEARCH:")
print("-" * 60)

test_queries = [
    "programma di 6 settimane con python",
    "seconda settimana corso python",
    "Python settimana 2",
    "fondamenti python data science"
]

for query in test_queries:
    print(f"\n  Query: '{query}'")

    # Raw query con distanze
    raw_results = vs.collection.query(
        query_texts=[query],
        n_results=3
    )

    if raw_results and raw_results['ids'] and raw_results['ids'][0]:
        for i in range(len(raw_results['ids'][0])):
            doc_id = raw_results['ids'][0][i]
            distance = raw_results['distances'][0][i] if 'distances' in raw_results else None
            content = raw_results['documents'][0][i][:100]

            print(f"    [{i+1}] ID: {doc_id}")
            print(f"        Distance: {distance:.4f}")
            print(f"        Content: {content}...")
    else:
        print("    ❌ Nessun risultato")

# 4. Verifica threshold
print("\n\n[4] ANALISI THRESHOLD:")
print("-" * 60)
print("  Config threshold: 0.7")
print("  Nota: ChromaDB usa distanza coseno (0 = identico, 2 = opposto)")
print("  Threshold 0.7 significa che vengono filtrati risultati con distanza > 0.7")
print("  Se le distanze sono > 0.7, nessun risultato passa il filtro!")

print("\n" + "=" * 60)
print("FINE DIAGNOSTICA")
print("=" * 60)
