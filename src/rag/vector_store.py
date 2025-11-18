"""
Vector Store Manager Module

Wrapper per ChromaDB che gestisce persistenza e operazioni sul vector database.

IMPORTANTE per STUDENTI:
- Usa PersistentClient (NON Client ephemeral!)
- I dati sopravvivono ai restart del bot
- Ogni documento è splittato in chunks con metadata
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
from datetime import datetime

from config import rag_config, paths_config
from src.utils.logger import get_logger
from src.utils.helpers import get_directory_size_mb

logger = get_logger(__name__)


class VectorStoreManager:
    """
    Gestore ChromaDB per persistenza documenti e retrieval.

    Responsabilità:
    1. Inizializzazione PersistentClient
    2. Creazione/gestione collection
    3. CRUD documenti (add, delete, list)
    4. Similarity search
    5. Statistiche database

    Example:
        >>> vs = VectorStoreManager()
        >>> vs.add_document(
        ...     chunks=["chunk1", "chunk2"],
        ...     metadatas=[{"page": 1}, {"page": 2}],
        ...     doc_id="doc_123"
        ... )
        >>> results = vs.similarity_search("query", k=3)
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        """
        Inizializza VectorStoreManager.

        ATTENZIONE STUDENTI:
        - persist_directory DEVE esistere e non essere temporaneo!
        - Usa PersistentClient, NON Client() che perde dati al restart

        Args:
            persist_directory: Path directory persistenza (default: da config)
            collection_name: Nome collection (default: da config)
        """
        self.persist_directory = persist_directory or paths_config.VECTORDB_DIR
        self.collection_name = collection_name or rag_config.COLLECTION_NAME

        logger.info(f"📦 Inizializzazione VectorStoreManager...")
        logger.info(f"   Directory: {self.persist_directory}")
        logger.info(f"   Collection: {self.collection_name}")

        # ========================================
        # CRITICAL: PersistentClient Setup
        # ========================================
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,  # Disabilita telemetria
                    allow_reset=False  # Sicurezza: non permettere reset accidentale
                )
            )
            logger.info("✅ ChromaDB PersistentClient inizializzato")

        except Exception as e:
            logger.error(f"❌ Errore inizializzazione ChromaDB: {e}")
            raise

        # ========================================
        # Collection Setup with OpenAI Embeddings
        # ========================================
        # IMPORTANTE: Configuriamo ChromaDB per usare OpenAI embeddings
        # invece del default (all-MiniLM-L6-v2 a 384 dims)
        try:
            # IMPORTANTE: ChromaDB con OpenAI richiede che gli embeddings
            # vengano passati esplicitamente via add(), NON via embedding_function
            # nella collection (bug/limitazione con OpenAI v1.x API)
            #
            # Quindi creiamo la collection SENZA embedding_function
            # e passeremo gli embeddings pre-calcolati in add_document()

            logger.info(f"   Embedding model: {rag_config.EMBEDDING_MODEL}")
            logger.info("   Note: Using explicit embeddings (not auto-generated)")

            # Get or create collection SENZA embedding_function
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "Educational bot documents collection",
                    "embedding_model": rag_config.EMBEDDING_MODEL,
                    "embedding_mode": "explicit"  # Embeddings passed explicitly
                }
            )
            logger.info(f"✅ Collection '{self.collection_name}' pronta")
            logger.info(f"   Chunks esistenti: {self.collection.count()}")

            # Initialize embedder once (reused across methods)
            from langchain_openai import OpenAIEmbeddings
            from config import api_keys

            self.embedder = OpenAIEmbeddings(
                model=rag_config.EMBEDDING_MODEL,
                openai_api_key=api_keys.OPENAI_API_KEY
            )
            logger.info("✅ OpenAI Embedder initialized")

        except Exception as e:
            logger.error(f"❌ Errore creazione collection: {e}")
            raise

    def add_document(
        self,
        chunks: List[str],
        metadatas: List[Dict[str, Any]],
        doc_id: str,
        embeddings: Optional[List[List[float]]] = None
    ) -> int:
        """
        Aggiunge documento al vector store.

        Il documento viene splittato in chunks, ognuno con metadata e ID univoco.

        Steps:
        1. Genera IDs univoci per ogni chunk (doc_id_chunk_0, doc_id_chunk_1, ...)
        2. Associa metadata (source, page, chunk_index, timestamp)
        3. Aggiunge a ChromaDB (genera embeddings automaticamente se non forniti)

        Args:
            chunks: Lista testi chunks
            metadatas: Lista metadata per ogni chunk
            doc_id: ID documento univoco
            embeddings: Embeddings pre-calcolati (opzionale)

        Returns:
            Numero chunks aggiunti

        Raises:
            ValueError: Se chunks e metadatas hanno lunghezze diverse

        Example:
            >>> chunks = ["text chunk 1", "text chunk 2"]
            >>> metadatas = [
            ...     {"source": "doc.pdf", "page": 1, "chunk_index": 0},
            ...     {"source": "doc.pdf", "page": 1, "chunk_index": 1}
            ... ]
            >>> num_added = vs.add_document(chunks, metadatas, "doc_123")
        """
        if len(chunks) != len(metadatas):
            raise ValueError(
                f"Chunks ({len(chunks)}) e metadatas ({len(metadatas)}) "
                "devono avere stessa lunghezza"
            )

        # Genera IDs univoci per ogni chunk
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]

        # Aggiungi timestamp a metadata
        timestamp = datetime.now().isoformat()
        for metadata in metadatas:
            metadata["doc_id"] = doc_id
            metadata["timestamp"] = timestamp

        logger.info(f"📝 Aggiunta documento '{doc_id}' con {len(chunks)} chunks...")

        try:
            # Se embeddings non forniti, calcolali con OpenAI
            if not embeddings:
                logger.info("   Calculating embeddings with OpenAI...")
                # Usa embedder pre-inizializzato (evita duplicazione)
                embeddings = self.embedder.embed_documents(chunks)
                logger.info(f"   ✅ Generated {len(embeddings)} embeddings")

            # Add to ChromaDB con embeddings espliciti
            self.collection.add(
                ids=chunk_ids,
                documents=chunks,
                metadatas=metadatas,
                embeddings=embeddings
            )

            logger.info(f"✅ Documento '{doc_id}' aggiunto con successo")
            return len(chunks)

        except Exception as e:
            logger.error(f"❌ Errore aggiunta documento: {e}")
            raise

    def delete_document(self, doc_id: str) -> int:
        """
        Elimina documento e tutti i suoi chunks dal vector store.

        Args:
            doc_id: ID documento da eliminare

        Returns:
            Numero chunks eliminati

        Example:
            >>> deleted_count = vs.delete_document("doc_123")
            >>> print(f"Eliminati {deleted_count} chunks")
        """
        logger.info(f"🗑️  Eliminazione documento '{doc_id}'...")

        try:
            # Query per trovare tutti chunks del documento
            results = self.collection.get(
                where={"doc_id": doc_id}
            )

            if not results or not results['ids']:
                logger.warning(f"⚠️  Documento '{doc_id}' non trovato")
                return 0

            num_chunks = len(results['ids'])

            # Delete by metadata filter
            self.collection.delete(
                where={"doc_id": doc_id}
            )

            logger.info(f"✅ Documento '{doc_id}' eliminato ({num_chunks} chunks)")
            return num_chunks

        except Exception as e:
            logger.error(f"❌ Errore eliminazione documento: {e}")
            raise

    def similarity_search(
        self,
        query: str,
        k: int = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Esegue similarity search sul vector store.

        Args:
            query: Query testuale dell'utente
            k: Numero risultati da restituire (default: da config)
            filter: Filtri metadata opzionali (es: {"source": "doc.pdf"})

        Returns:
            Lista di risultati con format:
            [
                {
                    "id": "doc_123_chunk_0",
                    "document": "text content",
                    "metadata": {"source": "doc.pdf", "page": 1, ...},
                    "distance": 0.85
                },
                ...
            ]

        Example:
            >>> results = vs.similarity_search("What is AI?", k=3)
            >>> for res in results:
            ...     print(f"Source: {res['metadata']['source']}")
            ...     print(f"Text: {res['document'][:100]}...")
        """
        if k is None:
            k = rag_config.TOP_K

        logger.debug(f"🔍 Similarity search: '{query}' (top-{k})")

        try:
            # Calcola embedding query con embedder pre-inizializzato
            query_embedding = self.embedder.embed_query(query)

            # Query ChromaDB con embedding esplicito
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filter
            )

            # Format results
            formatted_results = []

            if results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })

            logger.debug(f"✅ Trovati {len(formatted_results)} risultati")
            return formatted_results

        except Exception as e:
            logger.error(f"❌ Errore similarity search: {e}")
            return []

    def list_all_documents(self) -> List[Dict[str, Any]]:
        """
        Lista tutti i documenti caricati con metadata aggregati.

        Returns:
            Lista documenti con formato:
            [
                {
                    "doc_id": "doc_123",
                    "source": "example.pdf",
                    "summary": "Guida Python - variabili, loop, funzioni",
                    "num_chunks": 10,
                    "timestamp": "2025-01-04T...",
                    "pages": [1, 2, 3]
                },
                ...
            ]

        Example:
            >>> docs = vs.list_all_documents()
            >>> for doc in docs:
            ...     print(f"{doc['source']}: {doc['num_chunks']} chunks")
        """
        logger.debug("📋 Listing all documents...")

        try:
            # Get all items
            all_data = self.collection.get()

            if not all_data or not all_data['ids']:
                logger.info("📭 Nessun documento nel database")
                return []

            # Aggrega per doc_id
            docs_dict = {}

            for i, chunk_id in enumerate(all_data['ids']):
                metadata = all_data['metadatas'][i]
                doc_id = metadata.get('doc_id', 'unknown')

                if doc_id not in docs_dict:
                    docs_dict[doc_id] = {
                        "doc_id": doc_id,
                        "source": metadata.get('source', 'Unknown'),
                        "summary": metadata.get('summary', 'No summary available'),
                        "num_chunks": 0,
                        "timestamp": metadata.get('timestamp', 'N/A'),
                        "pages": set()
                    }

                docs_dict[doc_id]["num_chunks"] += 1

                # Aggiungi pagina se presente
                if 'page' in metadata:
                    docs_dict[doc_id]["pages"].add(metadata['page'])

            # Convert to list e format pages
            documents = []
            for doc_data in docs_dict.values():
                doc_data["pages"] = sorted(list(doc_data["pages"]))
                documents.append(doc_data)

            # Sort by timestamp (più recenti prima)
            documents.sort(
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )

            logger.info(f"✅ Trovati {len(documents)} documenti")
            return documents

        except Exception as e:
            logger.error(f"❌ Errore listing documents: {e}")
            return []

    def get_document_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Ottiene informazioni dettagliate su singolo documento.

        Args:
            doc_id: ID documento

        Returns:
            Dict con info documento o None se non trovato

        Example:
            >>> info = vs.get_document_info("doc_123")
            >>> if info:
            ...     print(f"Chunks: {info['num_chunks']}")
        """
        try:
            results = self.collection.get(
                where={"doc_id": doc_id}
            )

            if not results or not results['ids']:
                return None

            metadatas = results['metadatas']

            return {
                "doc_id": doc_id,
                "source": metadatas[0].get('source', 'Unknown'),
                "num_chunks": len(results['ids']),
                "timestamp": metadatas[0].get('timestamp', 'N/A'),
                "pages": sorted(set(m.get('page', 0) for m in metadatas))
            }

        except Exception as e:
            logger.error(f"❌ Errore get document info: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Ottiene statistiche del vector store.

        Returns:
            Dict con statistiche:
            {
                "total_chunks": 100,
                "total_documents": 10,
                "collection_name": "documents",
                "storage_size_mb": 50.5
            }

        Example:
            >>> stats = vs.get_stats()
            >>> print(f"Database ha {stats['total_documents']} documenti")
        """
        logger.debug("📊 Getting vector store stats...")

        try:
            total_chunks = self.collection.count()
            documents = self.list_all_documents()
            total_documents = len(documents)

            # Calcola dimensione storage
            storage_size_mb = get_directory_size_mb(self.persist_directory)

            stats = {
                "total_chunks": total_chunks,
                "total_documents": total_documents,
                "collection_name": self.collection_name,
                "storage_size_mb": round(storage_size_mb, 2)
            }

            logger.debug(f"✅ Stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"❌ Errore get stats: {e}")
            return {
                "total_chunks": 0,
                "total_documents": 0,
                "collection_name": self.collection_name,
                "storage_size_mb": 0.0
            }

    def update_document_summary(self, doc_id: str, new_summary: str) -> int:
        """
        Aggiorna il sommario di tutti i chunks di un documento.

        Args:
            doc_id: ID del documento
            new_summary: Nuovo sommario da applicare

        Returns:
            Numero di chunks aggiornati

        Example:
            >>> updated = vs.update_document_summary("doc_123", "Nuovo sommario")
            >>> print(f"Aggiornati {updated} chunks")
        """
        logger.info(f"🔄 Aggiornamento sommario per '{doc_id}'...")

        try:
            # Get all chunks for this document
            results = self.collection.get(
                where={"doc_id": doc_id}
            )

            if not results or not results['ids']:
                logger.warning(f"⚠️  Documento '{doc_id}' non trovato")
                return 0

            num_chunks = len(results['ids'])

            # Update metadata for each chunk
            for i, chunk_id in enumerate(results['ids']):
                # Get current metadata
                current_metadata = results['metadatas'][i]

                # Update summary field
                current_metadata['summary'] = new_summary

                # Update chunk with new metadata
                self.collection.update(
                    ids=[chunk_id],
                    metadatas=[current_metadata]
                )

            logger.info(f"✅ Sommario aggiornato per {num_chunks} chunks")
            return num_chunks

        except Exception as e:
            logger.error(f"❌ Errore aggiornamento sommario: {e}")
            raise

    def clear_all(self) -> bool:
        """
        DANGER: Elimina tutti i dati dal vector store.

        Usa con cautela! Azione irreversibile.

        Returns:
            True se successo

        Example:
            >>> if confirm_action():
            ...     vs.clear_all()
        """
        logger.warning("⚠️  CLEARING ALL DATA from vector store!")

        try:
            # Delete collection
            self.client.delete_collection(self.collection_name)

            # Recreate empty collection
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Educational bot documents collection"}
            )

            logger.info("✅ Vector store cleared")
            return True

        except Exception as e:
            logger.error(f"❌ Errore clear all: {e}")
            return False


if __name__ == "__main__":
    # Test VectorStoreManager
    print("Testing VectorStoreManager...\n")

    try:
        # Initialize
        vs = VectorStoreManager()

        # Test stats
        stats = vs.get_stats()
        print(f"Stats: {stats}")

        # Test list documents
        docs = vs.list_all_documents()
        print(f"\nDocuments: {len(docs)}")
        for doc in docs[:3]:  # Show first 3
            print(f"  - {doc['source']}: {doc['num_chunks']} chunks")

        print("\n✅ VectorStoreManager test completed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
