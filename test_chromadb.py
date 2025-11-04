"""
Test ChromaDB - Verifica RAG Pipeline senza API keys
Questo test NON richiede OpenAI/Telegram keys!
"""

import sys

print("\n" + "="*60)
print("TEST CHROMADB & RAG PIPELINE")
print("="*60 + "\n")

try:
    # Import componenti
    from src.rag.vector_store import VectorStoreManager
    from src.rag.document_processor import DocumentProcessor

    print("[1/8] Inizializzazione Vector Store...")
    vs = VectorStoreManager()
    print(f"      [OK] ChromaDB collection: '{vs.collection_name}'")
    print(f"      [OK] Persist directory: {vs.persist_directory}")

    print("\n[2/8] Inizializzazione Document Processor...")
    processor = DocumentProcessor()
    print(f"      [OK] Chunk size: {processor.chunk_size}")
    print(f"      [OK] Chunk overlap: {processor.chunk_overlap}")

    print("\n[3/8] Test Chunking di testo...")
    # Testo di esempio
    test_text = """
    Il machine learning è un ramo dell'intelligenza artificiale che si concentra
    sullo sviluppo di algoritmi che permettono ai computer di imparare dai dati.

    Ci sono tre tipi principali di machine learning:
    1. Supervised Learning: l'algoritmo impara da dati etichettati
    2. Unsupervised Learning: l'algoritmo trova pattern in dati non etichettati
    3. Reinforcement Learning: l'algoritmo impara attraverso tentativi ed errori

    Il deep learning è una sotto-categoria del machine learning che utilizza
    reti neurali artificiali con molti livelli (layers) per elaborare i dati.
    """ * 3  # Ripeti per avere abbastanza testo

    chunks = processor.chunk_text(test_text)
    print(f"      [OK] Creati {len(chunks)} chunks da {len(test_text)} caratteri")
    if chunks:
        avg_len = sum(len(c) for c in chunks) / len(chunks)
        print(f"      [OK] Lunghezza media chunk: {int(avg_len)} caratteri")
        print(f"      [OK] Primo chunk: '{chunks[0][:80]}...'")

    print("\n[4/8] Test Metadata Generation...")
    metadatas = []
    for i, chunk in enumerate(chunks):
        metadata = processor.create_metadata(
            filename="test_ml.txt",
            doc_id="doc_test_ml",
            chunk_index=i,
            page=1
        )
        metadatas.append(metadata)
    print(f"      [OK] Generati {len(metadatas)} metadata")
    print(f"      [OK] Esempio metadata: {metadatas[0]}")

    print("\n[5/8] Test Add Document to Vector Store...")
    num_added = vs.add_document(
        chunks=chunks,
        metadatas=metadatas,
        doc_id="doc_test_ml"
    )
    print(f"      [OK] Aggiunti {num_added} chunks al vector store")

    print("\n[6/8] Test Similarity Search...")
    # Query 1: Supervised learning
    query1 = "Cos'è il supervised learning?"
    print(f"      Query: '{query1}'")
    results1 = vs.similarity_search(query1, k=3)
    print(f"      [OK] Trovati {len(results1)} risultati rilevanti")
    if results1:
        print(f"      [OK] Risultato top: '{results1[0]['document'][:100]}...'")
        print(f"      [OK] Metadata: {results1[0]['metadata']['source']}")
        print(f"      [OK] Distance: {results1[0]['distance']:.3f}")

    # Query 2: Deep learning
    query2 = "Spiegami il deep learning"
    print(f"\n      Query: '{query2}'")
    results2 = vs.similarity_search(query2, k=3)
    print(f"      [OK] Trovati {len(results2)} risultati rilevanti")
    if results2:
        print(f"      [OK] Risultato top: '{results2[0]['document'][:100]}...'")
        print(f"      [OK] Distance: {results2[0]['distance']:.3f}")

    print("\n[7/8] Test List Documents...")
    docs = vs.list_all_documents()
    print(f"      [OK] Trovati {len(docs)} documenti nel sistema")
    for doc in docs:
        print(f"      - {doc['source']}: {doc['num_chunks']} chunks (ID: {doc['doc_id']})")

    print("\n[8/8] Test Statistics...")
    stats = vs.get_stats()
    print(f"      [OK] Statistiche Vector Store:")
    print(f"      - Totale documenti: {stats['total_documents']}")
    print(f"      - Totale chunks: {stats['total_chunks']}")
    print(f"      - Collection: {stats['collection_name']}")
    print(f"      - Storage: {stats['storage_size_mb']:.2f} MB")

    print("\n" + "="*60)
    print("[SUCCESS] RAG Pipeline funziona perfettamente!")
    print("="*60)

    print("\n[INFO] Vector database salvato in:")
    print(f"       {vs.persist_directory}")
    print("\n[NEXT] Puoi testare query aggiuntive o eliminare il test doc:")
    print("       vs.delete_document('doc_test_ml')")

except Exception as e:
    print(f"\n[ERROR] Test fallito: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
