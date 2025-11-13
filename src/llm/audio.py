"""
Audio TTS Module

Wrapper per OpenAI Text-to-Speech API.
Genera audio MP3 da testo per risposte vocali del bot.

IMPORTANTE per STUDENTI:
- TTS costa ~15x più del text generation!
- Limite: 4096 caratteri per request
- Usare solo se necessario (opt-in feature)
"""

from typing import Optional
from io import BytesIO

from config import llm_config
from src.utils.logger import get_logger
from src.utils.helpers import truncate_text
from src.utils.shared_clients import get_openai_client

logger = get_logger(__name__)


class AudioGenerator:
    """
    Generatore audio TTS usando OpenAI API.

    Features:
    1. Text-to-Speech con voce configurabile
    2. Gestione limite 4096 caratteri
    3. Output MP3 ottimizzato per Telegram
    4. Caching opzionale (TODO)

    Example:
        >>> audio_gen = AudioGenerator()
        >>> audio_bytes = audio_gen.generate("Hello world!")
        >>> # Send to Telegram
    """

    def __init__(
        self,
        voice: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Inizializza AudioGenerator.

        Args:
            voice: Nome voce OpenAI (default: da config)
                   Opzioni: alloy, echo, fable, onyx, nova, shimmer
            model: Modello TTS (default: da config)
                   Opzioni: tts-1 (standard), tts-1-hd (alta qualità)
        """
        self.voice = voice or llm_config.TTS_VOICE
        self.model = model or llm_config.TTS_MODEL
        self.max_chars = llm_config.TTS_MAX_CHARS

        logger.info(f"[INIT] AudioGenerator")
        logger.info(f"       Voice: {self.voice}")
        logger.info(f"       Model: {self.model}")
        logger.info(f"       Max chars: {self.max_chars}")

        # Use shared OpenAI client (evita duplicazioni)
        self.client = get_openai_client()

    def generate(
        self,
        text: str,
        auto_truncate: bool = True
    ) -> Optional[bytes]:
        """
        Genera audio MP3 da testo.

        ATTENZIONE:
        - OpenAI limit: 4096 caratteri
        - Se testo più lungo, viene troncato (se auto_truncate=True)
        - Costi: ~$15 per 1M caratteri con tts-1

        Args:
            text: Testo da convertire in audio
            auto_truncate: Se True, tronca automaticamente testo lungo

        Returns:
            Bytes MP3 audio o None se errore

        Raises:
            ValueError: Se testo troppo lungo e auto_truncate=False

        Example:
            >>> audio_bytes = audio_gen.generate("Hello, how are you?")
            >>> with open("output.mp3", "wb") as f:
            ...     f.write(audio_bytes)
        """
        if not text or len(text.strip()) == 0:
            logger.warning("[WARN] Empty text, skipping TTS")
            return None

        # Check length
        if len(text) > self.max_chars:
            if auto_truncate:
                logger.warning(f"[WARN] Text too long ({len(text)} chars), truncating to {self.max_chars}")
                text = truncate_text(text, max_tokens=self.max_chars, model="gpt-4o-mini")
            else:
                raise ValueError(
                    f"Text too long ({len(text)} chars). "
                    f"Max: {self.max_chars}. Use auto_truncate=True."
                )

        logger.info(f"[TTS] Generating audio for {len(text)} characters...")

        try:
            # Call OpenAI TTS API
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format="mp3"
            )

            # Get audio bytes
            audio_bytes = response.content

            logger.info(f"[OK] Generated {len(audio_bytes)} bytes MP3")
            return audio_bytes

        except Exception as e:
            logger.error(f"[ERROR] TTS generation failed: {e}")
            return None

    def generate_streaming(self, text: str):
        """
        Genera audio in streaming (per testi molto lunghi).

        NOTA: Implementazione futura per chunking automatico.

        Args:
            text: Testo lungo da convertire

        Yields:
            Chunks di audio bytes
        """
        # TODO: Implementare streaming per testi > 4096 chars
        # Splitta in chunks, genera audio per ognuno, concatena
        raise NotImplementedError("Streaming TTS not yet implemented")




if __name__ == "__main__":
    # Test AudioGenerator (requires valid API key)
    print("Testing AudioGenerator...\n")

    try:
        # Note: Questo test richiede una API key valida!
        audio_gen = AudioGenerator()
        print(f"[OK] AudioGenerator initialized")
        print(f"     Voice: {audio_gen.voice}")
        print(f"     Model: {audio_gen.model}")

        # Test text truncation logic
        long_text = "Hello world! " * 1000
        print(f"\n[TEST] Long text: {len(long_text)} chars")

        # Would truncate in real generation
        print(f"       Max allowed: {audio_gen.max_chars} chars")
        print(f"       Would truncate: {len(long_text) > audio_gen.max_chars}")

        print("\n[INFO] Skipping actual TTS call (requires API key)")
        print("       Set valid OPENAI_API_KEY to test generation")

        print("\n[SUCCESS] All tests passed!")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
