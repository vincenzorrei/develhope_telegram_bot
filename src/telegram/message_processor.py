"""
Message Processor Module

Processa messaggi utente (testo, immagini, audio) e genera risposte.
Integra LangChain, Vision, e TTS.
"""

from typing import Optional, Tuple
from src.utils.logger import get_logger
from src.llm.audio import AudioGenerator
from src.llm.image_processor import ImageProcessor

logger = get_logger(__name__)


class MessageProcessor:
    """
    Processore messaggi con integrazione multimodale.

    Features:
    1. Processamento testo con LangChain
    2. Analisi immagini con Vision
    3. Generazione audio con TTS
    """

    def __init__(self, langchain_engine):
        """
        Inizializza MessageProcessor.

        Args:
            langchain_engine: LangChainEngine instance
        """
        self.langchain_engine = langchain_engine
        self.audio_generator = AudioGenerator()
        self.image_processor = ImageProcessor()

        logger.info("[INIT] MessageProcessor ready")

    async def process_text(
        self,
        text: str,
        user_id: int,
        generate_audio: bool = False
    ) -> Tuple[str, Optional[bytes]]:
        """
        Processa messaggio testuale.

        Args:
            text: Testo utente
            user_id: Telegram user ID
            generate_audio: Se True, genera anche audio TTS

        Returns:
            Tuple (response_text, audio_bytes or None)
        """
        logger.info(f"[TEXT] Processing for user {user_id}")

        try:
            # Process con LangChain
            response = self.langchain_engine.process_message(
                user_message=text,
                user_id=user_id
            )

            # Generate audio se richiesto
            audio_bytes = None
            if generate_audio:
                logger.info("[TTS] Generating audio response...")
                audio_bytes = self.audio_generator.generate(response)

            return response, audio_bytes

        except Exception as e:
            logger.error(f"[ERROR] Text processing failed: {e}")
            return f"Errore: {str(e)[:200]}", None

    async def process_image(
        self,
        image_bytes: bytes,
        caption: Optional[str],
        user_id: int
    ) -> str:
        """
        Processa immagine con Vision.

        Args:
            image_bytes: Raw bytes immagine
            caption: Caption dell'utente (opzionale)
            user_id: Telegram user ID

        Returns:
            Analisi immagine
        """
        logger.info(f"[IMAGE] Processing for user {user_id}")

        try:
            if caption:
                # Visual Q&A
                analysis = self.image_processor.answer_question(
                    image_bytes=image_bytes,
                    question=caption
                )
            else:
                # Analisi generale
                analysis = self.image_processor.analyze_image(
                    image_bytes=image_bytes
                )

            return analysis or "Non sono riuscito ad analizzare l'immagine."

        except Exception as e:
            logger.error(f"[ERROR] Image processing failed: {e}")
            return f"Errore analisi immagine: {str(e)[:200]}"


if __name__ == "__main__":
    print("Message processor module loaded")
