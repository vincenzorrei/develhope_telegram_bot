"""
Image Processor Module

Wrapper per GPT-4o Vision API.
Analizza immagini con descrizioni, OCR, e Q&A visuale.

IMPORTANTE per STUDENTI:
- Vision costa uguale a text generation (no savings)
- Max 20MB per immagine
- Telegram comprime foto: meglio ricevere come "documento"
"""

import base64
from typing import Optional
from io import BytesIO

from config import llm_config
from prompts import prompts
from src.utils.logger import get_logger
from src.utils.shared_clients import get_openai_client

logger = get_logger(__name__)


class ImageProcessor:
    """
    Processore immagini con GPT-4o Vision.

    Features:
    1. Analisi immagini con descrizione dettagliata
    2. OCR (estrazione testo da immagini)
    3. Visual Q&A
    4. Context-aware processing

    Example:
        >>> processor = ImageProcessor()
        >>> description = processor.analyze_image(
        ...     image_bytes=image_data,
        ...     prompt="Describe this image in detail"
        ... )
    """

    def __init__(self, model: Optional[str] = None):
        """
        Inizializza ImageProcessor.

        Args:
            model: Modello Vision (default: gpt-4o from config)
        """
        self.model = model or llm_config.VISION_MODEL

        logger.info(f"[INIT] ImageProcessor")
        logger.info(f"       Model: {self.model}")

        # Use shared OpenAI client (evita duplicazioni)
        self.client = get_openai_client()

    def _encode_image(self, image_bytes: bytes) -> str:
        """
        Encode immagine in base64 per OpenAI API.

        Args:
            image_bytes: Raw bytes immagine

        Returns:
            Base64 encoded string

        Example:
            >>> encoded = processor._encode_image(image_data)
        """
        return base64.b64encode(image_bytes).decode('utf-8')

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        max_tokens: int = 500
    ) -> Optional[str]:
        """
        Analizza immagine con GPT-4o Vision.

        Args:
            image_bytes: Raw bytes dell'immagine
            prompt: Prompt custom (opzionale, usa default se None)
            max_tokens: Max tokens risposta

        Returns:
            Descrizione/analisi immagine o None se errore

        Example:
            >>> analysis = processor.analyze_image(
            ...     image_bytes=img_data,
            ...     prompt="What objects are in this image?"
            ... )
            >>> print(analysis)
        """
        if not image_bytes:
            logger.warning("[WARN] Empty image bytes")
            return None

        # Default prompt se non specificato
        if not prompt:
            # Usa prompt centralizzato da prompts.py
            prompt = prompts.VISION_ANALYSIS_PROMPT.format(caption="")

        logger.info(f"[VISION] Processing image ({len(image_bytes)} bytes)...")

        try:
            # Encode image
            base64_image = self._encode_image(image_bytes)

            # Create message with image
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=max_tokens
            )

            # Extract response
            analysis = response.choices[0].message.content

            logger.info(f"[OK] Generated {len(analysis)} chars analysis")
            return analysis

        except Exception as e:
            logger.error(f"[ERROR] Vision API failed: {e}")
            return None

    def extract_text(self, image_bytes: bytes) -> Optional[str]:
        """
        Estrae testo da immagine (OCR).

        Usa GPT-4o Vision per OCR più accurato di OCR tradizionale.

        Args:
            image_bytes: Raw bytes immagine

        Returns:
            Testo estratto o None

        Example:
            >>> text = processor.extract_text(screenshot_bytes)
            >>> print(f"Extracted: {text}")
        """
        ocr_prompt = """Estrai TUTTO il testo visibile in questa immagine.

Regole:
- Mantieni formattazione originale quando possibile
- Se tabella, preserva struttura
- Se codice, preserva indentazione
- Ignora elementi grafici/decorativi

Restituisci SOLO il testo estratto, senza commenti aggiuntivi."""

        return self.analyze_image(
            image_bytes=image_bytes,
            prompt=ocr_prompt,
            max_tokens=1000
        )

    def answer_question(
        self,
        image_bytes: bytes,
        question: str,
        max_tokens: int = 500
    ) -> Optional[str]:
        """
        Risponde a domanda su immagine (Visual Q&A).

        Args:
            image_bytes: Raw bytes immagine
            question: Domanda dell'utente
            max_tokens: Max tokens risposta

        Returns:
            Risposta o None

        Example:
            >>> answer = processor.answer_question(
            ...     image_bytes=diagram_bytes,
            ...     question="Spiega questo diagramma"
            ... )
        """
        # Usa prompt centralizzato da prompts.py
        qa_prompt = prompts.VISION_QUESTION_PROMPT.format(question=question)

        return self.analyze_image(
            image_bytes=image_bytes,
            prompt=qa_prompt,
            max_tokens=max_tokens
        )

    def describe_for_accessibility(self, image_bytes: bytes) -> Optional[str]:
        """
        Genera descrizione accessibile per screen readers.

        Args:
            image_bytes: Raw bytes immagine

        Returns:
            Descrizione accessibile

        Example:
            >>> alt_text = processor.describe_for_accessibility(img)
        """
        accessibility_prompt = """Genera una descrizione accessibile di questa immagine per utenti non vedenti.

Descrivi:
- Contenuto principale
- Layout e composizione
- Testo importante
- Contesto rilevante

Sii conciso ma completo (max 2-3 frasi)."""

        return self.analyze_image(
            image_bytes=image_bytes,
            prompt=accessibility_prompt,
            max_tokens=200
        )


if __name__ == "__main__":
    # Test ImageProcessor
    print("Testing ImageProcessor...\n")

    try:
        processor = ImageProcessor()
        print(f"[OK] ImageProcessor initialized")
        print(f"     Model: {processor.model}")

        # Test encoding (with dummy data)
        dummy_image = b"fake_image_data_for_testing"
        encoded = processor._encode_image(dummy_image)
        print(f"\n[TEST] Image encoding")
        print(f"       Input: {len(dummy_image)} bytes")
        print(f"       Encoded: {len(encoded)} chars base64")

        print("\n[INFO] Skipping actual Vision API call (requires API key + image)")
        print("       Set valid OPENAI_API_KEY and provide real image to test")

        print("\n[SUCCESS] Module tests passed!")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
