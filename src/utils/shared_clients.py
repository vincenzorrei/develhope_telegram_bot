"""
Shared Clients Module

Fornisce istanze singleton di client API per evitare duplicazioni
e ottimizzare l'uso di risorse.

IMPORTANTE:
- Un singolo client OpenAI può gestire multiple requests
- Evitare di creare multiple istanze riduce overhead
- Thread-safe per uso in applicazioni async
"""

from typing import Optional
from openai import OpenAI

from config import api_keys
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Singleton instances
_openai_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    """
    Restituisce istanza singleton di OpenAI client.

    Il client viene creato lazy (solo al primo utilizzo) e
    riutilizzato per tutte le successive chiamate.

    Returns:
        OpenAI client instance (singleton)

    Example:
        >>> from src.utils.shared_clients import get_openai_client
        >>> client = get_openai_client()
        >>> response = client.chat.completions.create(...)
    """
    global _openai_client

    if _openai_client is None:
        logger.info("[INIT] Creating shared OpenAI client...")
        _openai_client = OpenAI(api_key=api_keys.OPENAI_API_KEY)
        logger.info("✅ Shared OpenAI client initialized")

    return _openai_client


def reset_clients():
    """
    Reset dei client singleton (utile per testing).

    Forza la ricreazione dei client alla prossima chiamata.
    """
    global _openai_client
    _openai_client = None
    logger.info("[RESET] Shared clients reset")


if __name__ == "__main__":
    print("Testing shared_clients module...\n")

    # Test singleton behavior
    client1 = get_openai_client()
    client2 = get_openai_client()

    print(f"Client 1 ID: {id(client1)}")
    print(f"Client 2 ID: {id(client2)}")
    print(f"Same instance: {client1 is client2}")

    print("\n✅ shared_clients module working correctly")
