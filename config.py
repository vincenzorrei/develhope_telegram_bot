"""
Configuration Module - MUST be imported first!

Questo modulo contiene tutte le configurazioni del bot Telegram educativo.
IMPORTANTE: Include il workaround SQLite per ChromaDB su Replit.

Gli studenti possono modificare questo file per personalizzare:
- Admin user IDs
- Impostazioni LLM (model, temperature)
- Impostazioni RAG (chunk_size, top_k)
- Feature flags (voice mode, vision)
- Paths delle directory dati
"""

# ============================================
# CRITICAL: SQLite Workaround per Replit
# MUST be BEFORE any chromadb imports
# ============================================
import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    print("[OK] SQLite workaround attivato (pysqlite3)")
except ImportError:
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    print("[WARN] pysqlite3 non trovato, uso sqlite3 di sistema")

# ============================================
# Imports Standard
# ============================================
import os
from typing import List
from dotenv import load_dotenv

# Carica variabili d'ambiente da file .env (se esiste)
load_dotenv()


# ============================================
# API Keys (REQUIRED)
# ============================================
class APIKeys:
    """
    Gestione API keys da environment variables.

    Su Replit: usa Secrets invece di .env
    In locale: crea file .env dalla copia di .env.example
    """
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    @classmethod
    def validate(cls) -> bool:
        """
        Valida che tutte le API keys obbligatorie siano presenti.

        Returns:
            bool: True se tutte le keys sono presenti
        """
        missing = []
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")

        if missing:
            print(f"[ERROR] API Keys mancanti: {', '.join(missing)}")
            print(f"        Configura le keys in .env (locale) o Secrets (Replit)")
            return False

        if not cls.TAVILY_API_KEY:
            print("[WARN] TAVILY_API_KEY non configurato (web search disabilitato)")

        return True


# ============================================
# Admin Configuration
# ============================================
class AdminConfig:
    """
    Configurazione amministratori del bot.

    Solo gli user_id in questa lista possono:
    - Caricare documenti (/add_doc)
    - Eliminare documenti (/delete_doc)
    - Vedere statistiche sistema (/stats)
    - Gestire il database
    """
    # Lista user IDs admin (comma-separated in .env)
    ADMIN_USER_IDS: List[int] = [
        int(uid.strip())
        for uid in os.getenv("ADMIN_USER_IDS", "").split(",")
        if uid.strip().isdigit()
    ]

    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Verifica se user_id è admin"""
        return user_id in cls.ADMIN_USER_IDS


# ============================================
# Bot Settings
# ============================================
class BotConfig:
    """
    Impostazioni generali del bot Telegram.

    STUDENTI: Modificate queste impostazioni per sperimentare!
    """
    # Nome bot (per messaggi di benvenuto)
    BOT_NAME: str = "EduBot RAG"

    # Voice mode default (TTS attivo di default?)
    VOICE_MODE_DEFAULT: bool = False

    # Enable vision processing (GPT-4o Vision)
    VISION_ENABLED: bool = True

    # Enable web search (Tavily)
    WEB_SEARCH_ENABLED: bool = True

    # Max file size per upload (bytes) - Telegram limit è 20MB
    MAX_FILE_SIZE_MB: int = 20
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    # Polling vs Webhook
    USE_POLLING: bool = True  # True per Replit Free, False per webhook

    # Concurrent updates (gestione utenti simultanei)
    CONCURRENT_UPDATES: bool = True


# ============================================
# LLM Configuration
# ============================================
class LLMConfig:
    """
    Configurazione modelli LLM OpenAI.

    STUDENTI: Modificate temperature per cambiare creatività risposte!
    - temperature bassa (0.0-0.3): Risposte precise, deterministiche
    - temperature media (0.4-0.7): Bilanciato
    - temperature alta (0.8-1.0): Risposte creative, variabili
    """
    # Main chat model
    MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Temperature (creatività)
    TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))

    # Max tokens per risposta
    MAX_TOKENS: int = 1000

    # Vision model (per analisi immagini)
    VISION_MODEL: str = "gpt-4o"

    # TTS voice (alloy, echo, fable, onyx, nova, shimmer)
    TTS_VOICE: str = "nova"

    # TTS model
    TTS_MODEL: str = "tts-1"  # o "tts-1-hd" per qualità maggiore

    # Max caratteri TTS per singola request (limite OpenAI: 4096)
    TTS_MAX_CHARS: int = 4000


# ============================================
# RAG Configuration
# ============================================
class RAGConfig:
    """
    Configurazione Retrieval-Augmented Generation (RAG).

    STUDENTI: Sperimentate con questi parametri per ottimizzare retrieval!

    Chunk Size:
    - Piccolo (300-500): Più preciso ma perde contesto
    - Medio (600-1000): Bilanciato (RACCOMANDATO)
    - Grande (1000-2000): Più contesto ma meno preciso

    Top K:
    - Basso (1-3): Veloce, meno contesto
    - Medio (3-5): Bilanciato (RACCOMANDATO)
    - Alto (5-10): Più contesto ma più lento e costoso
    """
    # Embedding model
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # Document chunking
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))

    # Retrieval
    TOP_K: int = int(os.getenv("RAG_TOP_K", "3"))

    # Collection name in ChromaDB
    COLLECTION_NAME: str = "documents"

    # Similarity threshold (0.0-1.0, più alto = più simile richiesto)
    SIMILARITY_THRESHOLD: float = 0.7


# ============================================
# Memory Configuration
# ============================================
class MemoryConfig:
    """
    Configurazione memoria conversazionale.

    Sistema ibrido:
    - Short-term: ultimi N messaggi intatti
    - Long-term: riassunti automatici quando supera token_limit
    """
    # Token limit prima di summarization automatica
    TOKEN_LIMIT: int = int(os.getenv("MEMORY_TOKEN_LIMIT", "1500"))

    # Salva su disco ogni N messaggi
    SAVE_INTERVAL: int = int(os.getenv("MEMORY_SAVE_INTERVAL", "5"))

    # Max cached users in RAM (per performance)
    MAX_CACHED_USERS: int = 100


# ============================================
# Paths Configuration
# ============================================
class PathsConfig:
    """
    Configurazione percorsi directory dati.

    ATTENZIONE: Tutte le directory in data/ sono in .gitignore!
    """
    # Base data directory
    DATA_DIR: str = "./data"

    # ChromaDB vector store
    VECTORDB_DIR: str = os.path.join(DATA_DIR, "vectordb")

    # Uploaded documents (originali)
    DOCUMENTS_DIR: str = os.path.join(DATA_DIR, "documents")

    # User conversation memories
    CONVERSATIONS_DIR: str = os.path.join(DATA_DIR, "conversations")

    # Logs
    LOG_FILE: str = "bot.log"

    @classmethod
    def create_directories(cls) -> None:
        """Crea tutte le directory necessarie se non esistono"""
        directories = [
            cls.DATA_DIR,
            cls.VECTORDB_DIR,
            cls.DOCUMENTS_DIR,
            cls.CONVERSATIONS_DIR
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"[DIR] Verificata: {directory}")


# ============================================
# Logging Configuration
# ============================================
class LoggingConfig:
    """Configurazione logging"""
    LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


# ============================================
# LangChain Agent Configuration
# ============================================
class AgentConfig:
    """
    Configurazione LangChain Agent.

    STUDENTI: Sperimentate con max_iterations e verbose!
    """
    # Max iterations per agent execution
    MAX_ITERATIONS: int = 5

    # Verbose mode (stampa reasoning steps)
    VERBOSE: bool = True

    # Agent type
    AGENT_TYPE: str = "react"  # ReAct pattern

    # Early stopping method
    EARLY_STOPPING_METHOD: str = "generate"  # "force" or "generate"


# ============================================
# Feature Flags
# ============================================
class FeatureFlags:
    """
    Feature flags per abilitare/disabilitare funzionalità.

    Utile per debugging o deployment progressivo.
    """
    ENABLE_RAG: bool = True
    ENABLE_WEB_SEARCH: bool = True
    ENABLE_VISION: bool = True
    ENABLE_TTS: bool = True
    ENABLE_MEMORY: bool = True


# ============================================
# Rate Limiting Configuration
# ============================================
class RateLimitConfig:
    """
    Rate limiting per controllare costi API OpenAI.

    IMPORTANTE per uso educativo con molti studenti!
    """
    # Max queries per utente per giorno
    MAX_QUERIES_PER_USER_DAY: int = 100

    # Max TTS requests per utente per giorno
    MAX_TTS_PER_USER_DAY: int = 20

    # Max Vision requests per utente per giorno
    MAX_VISION_PER_USER_DAY: int = 10

    # Enable rate limiting
    ENABLE_RATE_LIMITING: bool = True


# ============================================
# Export Configurations
# ============================================
api_keys = APIKeys()
admin_config = AdminConfig()
bot_config = BotConfig()
llm_config = LLMConfig()
rag_config = RAGConfig()
memory_config = MemoryConfig()
paths_config = PathsConfig()
logging_config = LoggingConfig()
agent_config = AgentConfig()
feature_flags = FeatureFlags()
rate_limit_config = RateLimitConfig()


# ============================================
# Startup Validation
# ============================================
def validate_config() -> bool:
    """
    Valida configurazione all'avvio.

    Returns:
        bool: True se configurazione valida
    """
    print("\n" + "="*50)
    print("[CONFIG] VALIDAZIONE CONFIGURAZIONE")
    print("="*50)

    # Valida API keys
    if not api_keys.validate():
        return False

    # Valida admin config
    if not admin_config.ADMIN_USER_IDS:
        print("[WARN] Nessun admin configurato! Aggiungi ADMIN_USER_IDS in .env")
        return False

    print(f"[OK] Admin configurati: {len(admin_config.ADMIN_USER_IDS)}")
    print(f"[OK] LLM Model: {llm_config.MODEL}")
    print(f"[OK] Embedding Model: {rag_config.EMBEDDING_MODEL}")
    print(f"[OK] RAG Top-K: {rag_config.TOP_K}")
    print(f"[OK] Chunk Size: {rag_config.CHUNK_SIZE}")

    # Crea directories
    print("\n[INFO] Creazione directory...")
    paths_config.create_directories()

    print("\n[OK] Configurazione valida!")
    print("="*50 + "\n")

    return True


if __name__ == "__main__":
    # Test configuration
    validate_config()
