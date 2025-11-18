"""
Document Processor Module

Processa documenti (PDF, DOCX, TXT) per RAG:
1. Carica e estrae testo
2. Chunking intelligente
3. Genera metadata
4. Aggiunge al vector store

IMPORTANTE per STUDENTI:
- Usa pypdf (NON PyPDF2 deprecato!)
- Chunking con RecursiveCharacterTextSplitter
- Metadata include: source, page, chunk_index, timestamp
"""

import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

# Document loaders
import pypdf
from docx import Document

# LangChain text splitters
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import rag_config, paths_config
from src.utils.logger import get_logger
from src.utils.shared_clients import get_openai_client
from src.utils.helpers import (
    extract_file_extension,
    is_supported_document,
    sanitize_filename,
    generate_doc_id
)

logger = get_logger(__name__)


class DocumentProcessor:
    """
    Processore documenti per RAG pipeline.

    Responsabilità:
    1. Load documento (PDF/DOCX/TXT)
    2. Estrazione testo
    3. Chunking intelligente
    4. Generazione metadata
    5. Integrazione con VectorStoreManager

    Example:
        >>> processor = DocumentProcessor()
        >>> doc_id, num_chunks = processor.process_and_add(
        ...     filepath="document.pdf",
        ...     filename="document.pdf",
        ...     vector_store=vs
        ... )
        >>> print(f"Processed {num_chunks} chunks")
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        """
        Inizializza DocumentProcessor.

        Args:
            chunk_size: Dimensione chunk in caratteri (default: da config)
            chunk_overlap: Overlap tra chunks (default: da config)
        """
        self.chunk_size = chunk_size or rag_config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or rag_config.CHUNK_OVERLAP

        logger.info(f"[INIT] DocumentProcessor")
        logger.info(f"       Chunk size: {self.chunk_size}")
        logger.info(f"       Chunk overlap: {self.chunk_overlap}")

        # ========================================
        # Setup Text Splitter
        # ========================================
        # RecursiveCharacterTextSplitter cerca di splittare su:
        # 1. Paragrafi (\n\n)
        # 2. Righe singole (\n)
        # 3. Frasi (. )
        # 4. Parole ( )
        # 5. Caratteri singoli
        # In quest'ordine, mantenendo contesto semantico!
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        logger.info("[OK] Text splitter configured")

        # ========================================
        # Setup OpenAI client for summary generation
        # ========================================
        # Use shared OpenAI client (evita duplicazioni)
        self.openai_client = get_openai_client()

    def generate_summary(self, text: str, filename: str) -> str:
        """
        Genera sommario breve del documento usando LLM.

        Il sommario aiuta l'agent a decidere quando usare il RAG tool,
        fornendo visibilità sul contenuto dei documenti disponibili.

        Args:
            text: Testo completo del documento
            filename: Nome file per contesto

        Returns:
            Sommario breve (1-2 frasi, max 100 parole)

        Example:
            >>> summary = processor.generate_summary(text, "python_guide.pdf")
            >>> print(summary)
            "Guida Python - variabili, loop, funzioni, OOP"
        """
        logger.info(f"[SUMMARY] Generating summary for {filename}...")

        try:
            # Tronca testo se troppo lungo (max 4000 chars per efficienza)
            text_preview = text[:4000] if len(text) > 4000 else text

            prompt = f"""Genera un sommario MOLTO breve (max 100 parole) di questo documento.
Il sommario deve essere conciso e descrivere i temi principali trattati.

Documento: {filename}
Testo:
{text_preview}

Sommario (1-2 frasi max):"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Modello veloce ed economico
                messages=[
                    {"role": "system", "content": "Sei un assistente che genera sommari concisi di documenti."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3  # Deterministico
            )

            summary = response.choices[0].message.content.strip()
            logger.info(f"[OK] Summary: '{summary[:80]}...'")

            return summary

        except Exception as e:
            logger.error(f"[ERROR] Summary generation failed: {e}")
            # Fallback: usa inizio documento
            fallback = text[:200].replace("\n", " ").strip()
            return f"{filename} - {fallback}..."

    def load_pdf(self, filepath: str) -> Tuple[str, List[int]]:
        """
        Carica PDF e estrae testo.

        Usa pypdf (NON PyPDF2 deprecato!).

        Args:
            filepath: Path al file PDF

        Returns:
            Tuple (testo completo, lista numeri pagine)

        Raises:
            Exception: Se errore lettura PDF

        Example:
            >>> text, pages = processor.load_pdf("document.pdf")
            >>> print(f"Extracted {len(text)} chars from {len(pages)} pages")
        """
        logger.info(f"[PDF] Loading: {filepath}")

        try:
            text_content = ""
            page_numbers = []

            with open(filepath, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                num_pages = len(pdf_reader.pages)

                logger.info(f"      PDF has {num_pages} pages")

                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()

                    if page_text:
                        text_content += page_text + "\n\n"
                        page_numbers.append(page_num + 1)  # 1-indexed

            logger.info(f"[OK] Extracted {len(text_content)} characters")
            return text_content, page_numbers

        except Exception as e:
            logger.error(f"[ERROR] Failed to load PDF: {e}")
            raise

    def load_docx(self, filepath: str) -> str:
        """
        Carica DOCX e estrae testo.

        Usa python-docx.

        Args:
            filepath: Path al file DOCX

        Returns:
            Testo completo

        Raises:
            Exception: Se errore lettura DOCX

        Example:
            >>> text = processor.load_docx("document.docx")
        """
        logger.info(f"[DOCX] Loading: {filepath}")

        try:
            doc = Document(filepath)
            text_content = ""

            # Estrai testo da tutti i paragrafi
            for para in doc.paragraphs:
                if para.text.strip():
                    text_content += para.text + "\n\n"

            logger.info(f"[OK] Extracted {len(text_content)} characters")
            return text_content

        except Exception as e:
            logger.error(f"[ERROR] Failed to load DOCX: {e}")
            raise

    def load_txt(self, filepath: str) -> str:
        """
        Carica TXT e legge contenuto.

        Args:
            filepath: Path al file TXT

        Returns:
            Testo completo

        Raises:
            Exception: Se errore lettura TXT

        Example:
            >>> text = processor.load_txt("document.txt")
        """
        logger.info(f"[TXT] Loading: {filepath}")

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                text_content = file.read()

            logger.info(f"[OK] Extracted {len(text_content)} characters")
            return text_content

        except UnicodeDecodeError:
            # Fallback a latin-1 se UTF-8 fallisce
            logger.warning("[WARN] UTF-8 failed, trying latin-1")
            with open(filepath, 'r', encoding='latin-1') as file:
                text_content = file.read()
            return text_content

        except Exception as e:
            logger.error(f"[ERROR] Failed to load TXT: {e}")
            raise

    def load_md(self, filepath: str) -> str:
        """
        Carica Markdown (.md) e legge contenuto.

        Il Markdown viene trattato come testo plain, mantenendo
        la formattazione originale che può essere utile per il contesto.

        Args:
            filepath: Path al file MD

        Returns:
            Testo completo

        Raises:
            Exception: Se errore lettura MD

        Example:
            >>> text = processor.load_md("document.md")
        """
        logger.info(f"[MD] Loading: {filepath}")

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                text_content = file.read()

            logger.info(f"[OK] Extracted {len(text_content)} characters")
            return text_content

        except UnicodeDecodeError:
            # Fallback a latin-1 se UTF-8 fallisce
            logger.warning("[WARN] UTF-8 failed, trying latin-1")
            with open(filepath, 'r', encoding='latin-1') as file:
                text_content = file.read()
            return text_content

        except Exception as e:
            logger.error(f"[ERROR] Failed to load MD: {e}")
            raise

    def load_document(self, filepath: str, file_type: str) -> Tuple[str, Optional[List[int]]]:
        """
        Router per caricare documento in base al tipo.

        Args:
            filepath: Path al file
            file_type: Estensione file (pdf, docx, txt, md)

        Returns:
            Tuple (testo, lista pagine o None)

        Raises:
            ValueError: Se tipo file non supportato

        Example:
            >>> text, pages = processor.load_document("doc.pdf", "pdf")
        """
        file_type = file_type.lower()

        if file_type == "pdf":
            return self.load_pdf(filepath)
        elif file_type == "docx":
            text = self.load_docx(filepath)
            return text, None
        elif file_type == "txt":
            text = self.load_txt(filepath)
            return text, None
        elif file_type == "md":
            text = self.load_md(filepath)
            return text, None
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def chunk_text(self, text: str) -> List[str]:
        """
        Splitta testo in chunks usando RecursiveCharacterTextSplitter.

        Args:
            text: Testo da splittare

        Returns:
            Lista di chunks

        Example:
            >>> chunks = processor.chunk_text(long_text)
            >>> print(f"Created {len(chunks)} chunks")
        """
        logger.info(f"[CHUNK] Splitting text ({len(text)} chars)...")

        try:
            chunks = self.text_splitter.split_text(text)
            logger.info(f"[OK] Created {len(chunks)} chunks")

            # Log statistiche chunks
            if chunks:
                avg_length = sum(len(c) for c in chunks) / len(chunks)
                logger.info(f"      Avg chunk length: {int(avg_length)} chars")

            return chunks

        except Exception as e:
            logger.error(f"[ERROR] Chunking failed: {e}")
            raise

    def create_metadata(
        self,
        filename: str,
        doc_id: str,
        chunk_index: int,
        page: Optional[int] = None
    ) -> Dict:
        """
        Crea metadata dict per chunk.

        Metadata include:
        - source: nome file
        - doc_id: ID documento univoco
        - chunk_index: indice chunk (0-based)
        - page: numero pagina (se disponibile)
        - timestamp: timestamp creazione

        Args:
            filename: Nome file originale
            doc_id: ID documento
            chunk_index: Indice chunk
            page: Numero pagina (opzionale)

        Returns:
            Dict metadata

        Example:
            >>> metadata = processor.create_metadata(
            ...     filename="doc.pdf",
            ...     doc_id="doc_123",
            ...     chunk_index=0,
            ...     page=1
            ... )
        """
        metadata = {
            "source": filename,
            "doc_id": doc_id,
            "chunk_index": chunk_index,
            "timestamp": datetime.now().isoformat()
        }

        if page is not None:
            metadata["page"] = page

        return metadata

    def process_and_add(
        self,
        filepath: str,
        filename: str,
        vector_store
    ) -> Tuple[str, int, str]:
        """
        Pipeline completo: load → chunk → summary → metadata → add to vector store.

        Steps:
        1. Valida file supportato
        2. Carica e estrae testo
        3. Chunking
        4. Genera sommario documento (LLM)
        5. Genera metadata per ogni chunk
        6. Aggiunge a vector store
        7. Copia file in documents directory

        Args:
            filepath: Path completo al file
            filename: Nome file (per display)
            vector_store: VectorStoreManager instance

        Returns:
            Tuple (doc_id, numero chunks aggiunti, sommario documento)

        Raises:
            ValueError: Se file non supportato
            Exception: Se errore processing

        Example:
            >>> from src.rag.vector_store import VectorStoreManager
            >>> vs = VectorStoreManager()
            >>> processor = DocumentProcessor()
            >>> doc_id, num_chunks = processor.process_and_add(
            ...     filepath="/tmp/document.pdf",
            ...     filename="document.pdf",
            ...     vector_store=vs
            ... )
        """
        logger.info(f"[PROCESS] Starting pipeline for: {filename}")

        # ========================================
        # Step 1: Validazione
        # ========================================
        if not is_supported_document(filename):
            raise ValueError(f"Unsupported document type: {filename}")

        file_type = extract_file_extension(filename)

        # ========================================
        # Step 2: Load documento
        # ========================================
        text, pages = self.load_document(filepath, file_type)

        if not text or len(text.strip()) == 0:
            raise ValueError(f"Document is empty or could not be read: {filename}")

        # ========================================
        # Step 3: Chunking
        # ========================================
        chunks = self.chunk_text(text)

        if not chunks:
            raise ValueError(f"No chunks created from document: {filename}")

        # ========================================
        # Step 4: Genera doc_id e sommario
        # ========================================
        doc_id = generate_doc_id(filename)
        logger.info(f"[ID] Generated doc_id: {doc_id}")

        # Genera sommario documento (per system prompt)
        summary = self.generate_summary(text, filename)

        # ========================================
        # Step 5: Genera metadata per chunks
        # ========================================
        metadatas = []
        for i, chunk in enumerate(chunks):
            # Stima pagina per chunk (se disponibile)
            page_num = None
            if pages:
                # Stima approssimativa: chunk_index / num_chunks * num_pages
                estimated_page_idx = int((i / len(chunks)) * len(pages))
                if estimated_page_idx < len(pages):
                    page_num = pages[estimated_page_idx]

            metadata = self.create_metadata(
                filename=filename,
                doc_id=doc_id,
                chunk_index=i,
                page=page_num
            )
            # Aggiungi sommario ai metadata (per ogni chunk)
            metadata["summary"] = summary
            metadatas.append(metadata)

        # ========================================
        # Step 5: Add to vector store
        # ========================================
        logger.info(f"[VECTORDB] Adding {len(chunks)} chunks...")
        num_added = vector_store.add_document(
            chunks=chunks,
            metadatas=metadatas,
            doc_id=doc_id
        )

        # ========================================
        # Step 6: Copia file in documents directory
        # ========================================
        try:
            # Sanitize filename
            safe_filename = sanitize_filename(filename)
            dest_path = os.path.join(
                paths_config.DOCUMENTS_DIR,
                f"{doc_id}_{safe_filename}"
            )

            # Copia file
            import shutil
            shutil.copy2(filepath, dest_path)
            logger.info(f"[COPY] Saved to: {dest_path}")

        except Exception as e:
            logger.warning(f"[WARN] Could not copy file: {e}")
            # Non bloccare se copia fallisce

        logger.info(f"[SUCCESS] Processed document")
        logger.info(f"          Doc ID: {doc_id}")
        logger.info(f"          Chunks: {num_added}")
        logger.info(f"          Summary: {summary[:80]}...")

        return doc_id, num_added, summary


if __name__ == "__main__":
    # Test DocumentProcessor
    print("Testing DocumentProcessor...\n")

    try:
        # Initialize
        processor = DocumentProcessor()
        print(f"[OK] Processor initialized")
        print(f"     Chunk size: {processor.chunk_size}")
        print(f"     Overlap: {processor.chunk_overlap}")

        # Test chunking
        test_text = """
        Lorem ipsum dolor sit amet, consectetur adipiscing elit.
        Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

        Ut enim ad minim veniam, quis nostrud exercitation ullamco.
        Laboris nisi ut aliquip ex ea commodo consequat.
        """ * 10  # Ripeti per avere testo lungo

        chunks = processor.chunk_text(test_text)
        print(f"\n[OK] Chunking test:")
        print(f"     Input: {len(test_text)} chars")
        print(f"     Output: {len(chunks)} chunks")
        if chunks:
            print(f"     First chunk: {chunks[0][:100]}...")

        # Test metadata creation
        metadata = processor.create_metadata(
            filename="test.pdf",
            doc_id="doc_test",
            chunk_index=0,
            page=1
        )
        print(f"\n[OK] Metadata test:")
        print(f"     {metadata}")

        print("\n[SUCCESS] All tests passed!")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
