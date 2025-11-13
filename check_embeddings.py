"""Check ChromaDB collection embedding dimensions"""
import chromadb

client = chromadb.PersistentClient(path='./data/vectordb')
coll = client.get_collection('documents')

print(f"Collection: {coll.name}")
print(f"Metadata: {coll.metadata}")
print(f"Count: {coll.count()}")

# Get one document with embeddings
results = coll.get(limit=1, include=['embeddings', 'metadatas'])

if results['embeddings'] is not None and len(results['embeddings']) > 0:
    embedding_dims = len(results['embeddings'][0])
    print(f"\nEmbedding dimensions: {embedding_dims}")

    if embedding_dims == 384:
        print("→ Uses ChromaDB default (all-MiniLM-L6-v2)")
    elif embedding_dims == 1536:
        print("→ Uses OpenAI text-embedding-3-large or text-embedding-ada-002")
    elif embedding_dims == 1024:
        print("→ Uses text-embedding-3-small (default dimensions)")
    elif embedding_dims == 768:
        print("→ Uses text-embedding-3-large (reduced)")
    else:
        print(f"→ Custom embedding model ({embedding_dims} dims)")
else:
    print("\nNo embeddings found!")
