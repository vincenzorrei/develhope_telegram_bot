"""
Message Processor Module

Processa messaggi utente (testo, immagini, audio) e genera risposte.
Integra LangChain, Vision, TTS e Speech-to-Text (Whisper).
"""

from typing import Optional, Tuple
from openai import OpenAI
from config import api_keys, AgentConfig
from src.utils.logger import get_logger
from src.utils.helpers import convert_markdown_to_html
from src.llm.audio import AudioGenerator
from src.llm.image_processor import ImageProcessor

logger = get_logger(__name__)
client = OpenAI(api_key=api_keys.OPENAI_API_KEY)


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

    def _is_valid_response(self, response: Optional[str]) -> bool:
        """
        Valida se una risposta del LLM è accettabile.

        Una risposta valida deve:
        - Esistere (not None/empty)
        - Essere sufficientemente lunga (> 100 chars)
        - Non contenere messaggi di errore generici

        Args:
            response: Risposta da validare

        Returns:
            True se valida, False altrimenti
        """
        if not response:
            return False

        return (
            len(response) > 100 and
            "errore" not in response.lower()[:50]  # Check solo inizio risposta
        )

    async def _try_fallback_rag(self, text: str) -> str:
        """
        Esegue fallback usando RAG diretto (bypass agent).

        Questo metodo viene usato quando l'agent ReAct fallisce
        ripetutamente, fornendo una risposta diretta dai documenti.

        Args:
            text: Query utente

        Returns:
            Risposta da RAG diretto o messaggio di errore
        """
        logger.info(f"🔧 [FALLBACK] Using direct RAG search (bypassing agent)...")
        try:
            response = await self.langchain_engine._search_documents(text)
            logger.info(f"✅ [FALLBACK] Direct RAG succeeded ({len(response)} chars)")
            return response
        except Exception as e:
            logger.error(f"❌ [ERROR] Fallback also failed: {e}")
            return "Mi dispiace, ho riscontrato problemi tecnici. Riprova tra poco."

    async def process_text(
        self,
        text: str,
        user_id: int,
        generate_audio: bool = False
    ) -> Tuple[str, Optional[bytes]]:
        """
        Processa messaggio testuale (ASYNC) con retry automatico.

        Strategia resilienza:
        1. Tentativo 1-N: Agent normale con ReAct pattern
        2. Fallback: RAG diretto (bypass agent) se parsing errors persistono

        Args:
            text: Testo utente
            user_id: Telegram user ID
            generate_audio: Se True, genera anche audio TTS

        Returns:
            Tuple (response_text, audio_bytes or None)
        """
        logger.info(f"[TEXT] Processing for user {user_id}")

        response = None
        max_retries = AgentConfig.MAX_RETRIES

        # ========================================
        # Retry Loop con Agent
        # ========================================
        for attempt in range(max_retries + 1):
            try:
                # Process con LangChain Agent (ASYNC)
                response = await self.langchain_engine.process_message(
                    user_message=text,
                    user_id=user_id
                )

                # Verifica se risposta è valida usando helper method
                if self._is_valid_response(response):
                    logger.info(f"✅ [TEXT] Agent succeeded on attempt {attempt + 1}/{max_retries + 1}")
                    break  # Success!
                else:
                    logger.warning(f"⚠️  [TEXT] Agent response invalid (len={len(response) if response else 0}) on attempt {attempt + 1}/{max_retries + 1}")
                    if attempt < max_retries:
                        logger.info(f"🔄 [TEXT] Retrying...")
                        response = None  # Clear for retry
                        continue
                    else:
                        logger.warning(f"⚠️  [TEXT] Max retries reached, trying fallback...")
                        response = None  # Force fallback

            except Exception as e:
                logger.error(f"❌ [ERROR] Agent failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    logger.info(f"🔄 [TEXT] Retrying after exception...")
                    continue
                else:
                    logger.warning(f"⚠️  [TEXT] Max retries reached after exceptions")
                    response = None  # Force fallback

        # ========================================
        # Fallback: RAG Diretto (Bypass Agent)
        # ========================================
        # Se dopo retry la risposta è ancora invalida, usa RAG diretto
        if not self._is_valid_response(response):
            logger.info(f"    Reason: response={'None' if not response else f'{len(response)} chars'}")
            response = await self._try_fallback_rag(text)

        # ========================================
        # Post-Processing
        # ========================================
        try:
            # Convert Markdown to HTML (UNICO PUNTO DI CONVERSIONE)
            response = convert_markdown_to_html(response)

            # Generate audio se richiesto
            audio_bytes = None
            if generate_audio:
                logger.info("[TTS] Generating audio response...")
                audio_bytes = self.audio_generator.generate(response)

            return response, audio_bytes

        except Exception as e:
            logger.error(f"[ERROR] Post-processing failed: {e}")
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

            result = analysis or "Non sono riuscito ad analizzare l'immagine."

            # Convert Markdown to HTML (fallback se LLM ignora istruzioni)
            result = convert_markdown_to_html(result)

            return result

        except Exception as e:
            logger.error(f"[ERROR] Image processing failed: {e}")
            return f"Errore analisi immagine: {str(e)[:200]}"

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        audio_format: str = "ogg"
    ) -> Optional[str]:
        """
        Trascrivi messaggio vocale usando OpenAI Whisper.

        Args:
            audio_bytes: Raw bytes del file audio
            audio_format: Formato audio (ogg, mp3, wav, etc.)

        Returns:
            Testo trascritto o None se errore

        Example:
            >>> text = await processor.transcribe_audio(audio_bytes, "ogg")
            >>> print(f"Transcription: {text}")
        """
        logger.info(f"[WHISPER] Transcribing audio ({len(audio_bytes)} bytes)...")

        try:
            # Salva temporaneamente audio in file-like object
            import io
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = f"voice_message.{audio_format}"

            # Whisper API transcription
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="it"  # Italiano (opzionale, Whisper auto-detect)
            )

            transcribed_text = transcription.text

            logger.info(f"[WHISPER] Transcribed: '{transcribed_text[:100]}...'")
            return transcribed_text

        except Exception as e:
            logger.error(f"[ERROR] Whisper transcription failed: {e}")
            return None


if __name__ == "__main__":
    print("Message processor module loaded")
