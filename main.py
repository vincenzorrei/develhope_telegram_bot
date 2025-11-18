"""
Main Entry Point - Bot Telegram Educativo con RAG

Questo è il file principale da eseguire per avviare il bot.

Uso:
    python main.py

Requisiti:
    - Python 3.11
    - Dipendenze installate: pip install -r requirements.txt
    - API keys configurate in .env (locale) o Environment Variables (Railway)
    - Admin user IDs configurati

Flow di avvio:
    1. Setup SQLite workaround (già in config.py)
    2. Validazione configurazione
    3. Inizializzazione componenti:
       - VectorStore (ChromaDB)
       - DocumentProcessor
       - LangChainEngine
       - MessageProcessor
       - Telegram Bot
    4. Registrazione handlers
    5. Avvio polling
    6. Graceful shutdown su CTRL+C
"""

import sys
import signal
from src.utils.logger import main_logger, log_startup_info, log_shutdown_info

# Import config (triggers SQLite workaround)
import config

# Validate configuration
if not config.validate_config():
    print("\n[ERROR] Configuration validation failed!")
    print("        Check your .env file or Railway Environment Variables")
    sys.exit(1)

# Imports dopo validazione config
from bot_engine import LangChainEngine
from src.rag.vector_store import VectorStoreManager
from src.rag.document_processor import DocumentProcessor
from src.telegram.bot_setup import create_bot
from src.telegram.message_processor import MessageProcessor
from src.telegram.handlers import setup_handlers


def initialize_components():
    """
    Inizializza tutti i componenti del bot.

    Returns:
        Dict con tutti i componenti inizializzati

    Raises:
        Exception: Se inizializzazione fallisce
    """
    main_logger.info("\n" + "="*60)
    main_logger.info("INITIALIZING COMPONENTS")
    main_logger.info("="*60)

    components = {}

    try:
        # ========================================
        # 1. Vector Store (ChromaDB)
        # ========================================
        main_logger.info("\n[1/5] Initializing Vector Store...")
        vector_store = VectorStoreManager()
        components['vector_store'] = vector_store
        main_logger.info("[OK] Vector Store ready")

        # ========================================
        # 2. Document Processor
        # ========================================
        main_logger.info("\n[2/5] Initializing Document Processor...")
        document_processor = DocumentProcessor()
        components['document_processor'] = document_processor
        main_logger.info("[OK] Document Processor ready")

        # ========================================
        # 3. LangChain Engine (CORE)
        # ========================================
        main_logger.info("\n[3/5] Initializing LangChain Engine...")
        langchain_engine = LangChainEngine(vector_store)
        components['langchain_engine'] = langchain_engine
        main_logger.info("[OK] LangChain Engine ready")

        # ========================================
        # 4. Message Processor
        # ========================================
        main_logger.info("\n[4/5] Initializing Message Processor...")
        message_processor = MessageProcessor(langchain_engine)
        components['message_processor'] = message_processor
        main_logger.info("[OK] Message Processor ready")

        # ========================================
        # 5. Telegram Bot
        # ========================================
        main_logger.info("\n[5/5] Initializing Telegram Bot...")
        app = create_bot()
        components['app'] = app
        main_logger.info("[OK] Telegram Bot ready")

        main_logger.info("\n" + "="*60)
        main_logger.info("ALL COMPONENTS INITIALIZED SUCCESSFULLY")
        main_logger.info("="*60 + "\n")

        return components

    except Exception as e:
        main_logger.error(f"\n[FATAL] Component initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def setup_signal_handlers(components=None):
    """
    Setup gestione segnali per graceful shutdown.

    Gestisce CTRL+C e SIGTERM per chiusura pulita.

    Args:
        components: Dict dei componenti inizializzati (per save-on-shutdown)
    """
    def signal_handler(sig, frame):
        """Handler per CTRL+C con graceful shutdown"""
        main_logger.info("\n\n[SHUTDOWN] Received interrupt signal")

        # Session store is in-memory, no need to save to disk
        if components and 'langchain_engine' in components:
            try:
                session_count = len(components['langchain_engine'].session_store)
                main_logger.info(f"[SHUTDOWN] Clearing {session_count} active session(s)...")
                main_logger.info(f"[OK] Session store will be cleared on exit")
            except Exception as e:
                main_logger.error(f"[ERROR] Failed to check sessions: {e}")

        log_shutdown_info()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """
    Main function - entry point del bot.

    Steps:
    1. Log startup info
    2. Setup signal handlers
    3. Initialize components
    4. Setup handlers
    5. Start polling
    6. Run forever (until CTRL+C)
    """
    # ========================================
    # Startup
    # ========================================
    log_startup_info()

    main_logger.info("Starting Telegram Educational Bot with RAG...")
    main_logger.info(f"Bot name: {config.bot_config.BOT_NAME}")
    main_logger.info(f"Admins: {len(config.admin_config.ADMIN_USER_IDS)}")

    # ========================================
    # Initialize all components
    # ========================================
    components = initialize_components()

    # ========================================
    # Setup signal handlers (with components for graceful shutdown)
    # ========================================
    setup_signal_handlers(components=components)

    # ========================================
    # Session store info (in-memory, no cleanup needed)
    # ========================================
    main_logger.info("[OK] Session store initialized (in-memory)")
    main_logger.info(f"     Summary buffer threshold: {config.memory_config.MAX_TOKENS_BEFORE_SUMMARY} tokens")

    # ========================================
    # Setup handlers
    # ========================================
    main_logger.info("Setting up Telegram handlers...")

    # Config data per handlers
    config_data = {
        'llm_model': config.llm_config.MODEL,
        'embedding_model': config.rag_config.EMBEDDING_MODEL,
        'rag_top_k': config.rag_config.TOP_K
    }

    setup_handlers(
        app=components['app'],
        langchain_engine=components['langchain_engine'],
        vector_store=components['vector_store'],
        document_processor=components['document_processor'],
        message_processor=components['message_processor'],
        config_data=config_data
    )

    main_logger.info("[OK] Handlers configured")

    # ========================================
    # Start Bot
    # ========================================
    main_logger.info("\n" + "="*60)
    main_logger.info("BOT STARTING - POLLING MODE")
    main_logger.info("="*60)
    main_logger.info("Bot is now running! Press CTRL+C to stop.")
    main_logger.info("="*60 + "\n")

    try:
        # Run bot with polling
        components['app'].run_polling(
            allowed_updates=['message', 'callback_query']
        )

    except Exception as e:
        main_logger.error(f"\n[FATAL] Bot crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    """
    Entry point quando eseguito direttamente.

    Usage:
        python main.py
    """
    main()
