"""
Retriever Module

Wrapper per query sul vector store con logica RAG avanzata.
Include filtering, re-ranking, e formatting dei risultati.
"""

from typing import List, Dict, Optional, Any
from config import rag_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Retriever:
    """
    Retriever per query RAG sul vector store.

    Funzionalità:
    1. Similarity search base
    2. Filtering per metadata
    3. Formatting risultati con citazioni
    4. Score threshold filtering

    Example:
        >>> retriever = Retriever(vector_store)
        >>> results = retriever.retrieve("What is AI?", k=3)
        >>> for res in results:
        ...     print(res['document'][:100])
    """

    def __init__(self, vector_store):
        """
        Inizializza Retriever.

        Args:
            vector_store: VectorStoreManager instance
        """
        self.vector_store = vector_store
        self.top_k = rag_config.TOP_K
        self.similarity_threshold = rag_config.SIMILARITY_THRESHOLD

        logger.info(f"[INIT] Retriever")
        logger.info(f"       Top-K: {self.top_k}")
        logger.info(f"       Threshold: {self.similarity_threshold}")

    def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Esegue retrieval dal vector store.

        Args:
            query: Query testuale
            k: Numero risultati (default: da config)
            filter_metadata: Filtri metadata (es: {"source": "doc.pdf"})
            min_score: Score minimo (default: da config)

        Returns:
            Lista risultati con format:
            [
                {
                    "id": "doc_123_chunk_0",
                    "document": "text content",
                    "metadata": {...},
                    "distance": 0.85,
                    "score": 0.15  # 1 - distance
                },
                ...
            ]

        Example:
            >>> results = retriever.retrieve(
            ...     query="What is machine learning?",
            ...     k=5,
            ...     filter_metadata={"source": "ml_book.pdf"}
            ... )
        """
        k = k or self.top_k
        min_score = min_score or (1 - self.similarity_threshold)

        logger.debug(f"[RETRIEVE] Query: '{query[:50]}...'")
        logger.debug(f"           Top-K: {k}, Min score: {min_score}")

        try:
            # Query vector store
            results = self.vector_store.similarity_search(
                query=query,
                k=k,
                filter=filter_metadata
            )

            # Add score field (1 - distance)
            for result in results:
                if result.get('distance') is not None:
                    result['score'] = 1 - result['distance']
                else:
                    result['score'] = 1.0

            # Filter by min_score
            filtered_results = [
                r for r in results
                if r['score'] >= min_score
            ]

            logger.debug(f"[OK] Retrieved {len(filtered_results)} results (filtered from {len(results)})")

            return filtered_results

        except Exception as e:
            logger.error(f"[ERROR] Retrieval failed: {e}")
            return []

    def format_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Formatta risultati retrieval in context string per LLM.

        Args:
            results: Lista risultati da retrieve()

        Returns:
            Context string formattato

        Example:
            >>> results = retriever.retrieve("query")
            >>> context = retriever.format_context(results)
            >>> # Use in prompt
        """
        if not results:
            return ""

        context_parts = []

        for i, result in enumerate(results, 1):
            text = result.get('document', '')

            context_part = f"""
Document {i}:
Content: {text}
"""
            context_parts.append(context_part.strip())

        return "\n\n---\n\n".join(context_parts)

    def format_sources(self, results: List[Dict[str, Any]]) -> str:
        """
        Formatta citazioni fonti per risposta utente.

        Args:
            results: Lista risultati da retrieve()

        Returns:
            String con citazioni formattate

        Example:
            >>> sources = retriever.format_sources(results)
            >>> response = answer + "\n\n" + sources
        """
        if not results:
            return ""

        citations = "\n\n**Fonti:**\n"

        # Raggruppa per source
        sources_set = set()
        for result in results:
            metadata = result.get('metadata', {})
            source = metadata.get('source', 'Unknown')
            page = metadata.get('page')

            if page:
                sources_set.add(f"{source} (pag. {page})")
            else:
                sources_set.add(source)

        for i, source in enumerate(sorted(sources_set), 1):
            citations += f"{i}. {source}\n"

        return citations



if __name__ == "__main__":
    print("Retriever module loaded successfully")
