"""
Logger Configuration Module

Setup logging centralizzato per il bot Telegram educativo.
Supporta logging su file e console con formattazione personalizzata.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from config import logging_config, paths_config


class ColoredFormatter(logging.Formatter):
    """
    Formatter con colori per output console.

    Migliora leggibilità dei log durante development.
    """

    # Codici colore ANSI
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record):
        """Formatta record con colori se terminale lo supporta"""
        # Aggiungi colore al livello
        levelname = record.levelname
        if levelname in self.COLORS and sys.stderr.isatty():
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )

        return super().format(record)


def setup_logger(
    name: str = "telegram_bot",
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Configura e restituisce logger personalizzato.

    Args:
        name: Nome del logger
        level: Livello logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path file log (opzionale)
        console: Se True, logga anche su console

    Returns:
        Logger configurato

    Example:
        >>> logger = setup_logger("my_module", level="DEBUG")
        >>> logger.info("Test message")
    """
    # Ottieni o crea logger
    logger = logging.getLogger(name)

    # Evita duplicazione handler se già configurato
    if logger.handlers:
        return logger

    # Imposta livello
    log_level = level or logging_config.LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))

    # Formato log
    log_format = logging_config.FORMAT
    date_format = logging_config.DATE_FORMAT

    # ========================================
    # Handler Console (se richiesto)
    # ========================================
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # Usa formatter con colori per console
        console_formatter = ColoredFormatter(
            log_format,
            datefmt=date_format
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # ========================================
    # Handler File (se specificato)
    # ========================================
    if log_file:
        # Crea directory log se non esiste
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            log_file,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # Formatter senza colori per file
        file_formatter = logging.Formatter(
            log_format,
            datefmt=date_format
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Previeni propagazione a root logger (evita duplicati)
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Ottieni logger esistente o creane uno nuovo.

    Convenienza per ottenere logger senza riconfigurare.

    Args:
        name: Nome del logger

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger("my_module")
        >>> logger.info("Message")
    """
    logger = logging.getLogger(name)

    # Se non ha handler, configuralo
    if not logger.handlers:
        return setup_logger(
            name=name,
            log_file=paths_config.LOG_FILE,
            console=True
        )

    return logger


class LoggerMixin:
    """
    Mixin per aggiungere logging automatico alle classi.

    Usage:
        class MyClass(LoggerMixin):
            def my_method(self):
                self.logger.info("Log message")
    """

    @property
    def logger(self) -> logging.Logger:
        """Lazy logger per la classe"""
        name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        return get_logger(name)


def log_function_call(func):
    """
    Decorator per loggare chiamate a funzioni.

    Utile per debugging.

    Example:
        @log_function_call
        def my_function(x, y):
            return x + y
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(
            f"Calling {func.__name__}() with args={args}, kwargs={kwargs}"
        )

        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__}() returned {result}")
            return result
        except Exception as e:
            logger.error(
                f"{func.__name__}() raised {type(e).__name__}: {e}",
                exc_info=True
            )
            raise

    return wrapper


def log_execution_time(func):
    """
    Decorator per loggare tempo di esecuzione funzione.

    Utile per performance monitoring.

    Example:
        @log_execution_time
        def slow_function():
            time.sleep(2)
    """
    import time

    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(
                f"{func.__name__}() executed in {elapsed:.2f}s"
            )
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"{func.__name__}() failed after {elapsed:.2f}s: {e}"
            )
            raise

    return wrapper


# ========================================
# Default Logger Instance
# ========================================
# Logger principale per il bot
main_logger = setup_logger(
    name="telegram_bot",
    log_file=paths_config.LOG_FILE,
    console=True
)


# ========================================
# Utility Functions
# ========================================

def log_startup_info():
    """Logga informazioni di startup del bot"""
    main_logger.info("=" * 60)
    main_logger.info("🤖 TELEGRAM BOT EDUCATIVO CON RAG")
    main_logger.info("=" * 60)
    main_logger.info(f"📅 Avvio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    main_logger.info(f"🐍 Python: {sys.version.split()[0]}")
    main_logger.info(f"📝 Log file: {paths_config.LOG_FILE}")
    main_logger.info(f"🔧 Log level: {logging_config.LEVEL}")
    main_logger.info("=" * 60)


def log_shutdown_info():
    """Logga informazioni di shutdown del bot"""
    main_logger.info("=" * 60)
    main_logger.info("🛑 SHUTDOWN BOT")
    main_logger.info(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    main_logger.info("=" * 60)


def log_error_with_context(error: Exception, context: dict):
    """
    Logga errore con contesto aggiuntivo per debugging.

    Args:
        error: Eccezione da loggare
        context: Dict con info contesto (user_id, query, etc.)

    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     log_error_with_context(e, {"user_id": 123, "query": "test"})
    """
    main_logger.error(
        f"Error: {type(error).__name__}: {error}",
        exc_info=True
    )
    main_logger.error(f"Context: {context}")


# ========================================
# Emoji Logging Helpers
# ========================================

def log_success(message: str):
    """Logga successo con emoji"""
    main_logger.info(f"✅ {message}")


def log_warning(message: str):
    """Logga warning con emoji"""
    main_logger.warning(f"⚠️  {message}")


def log_error(message: str):
    """Logga errore con emoji"""
    main_logger.error(f"❌ {message}")


def log_info(message: str):
    """Logga info con emoji"""
    main_logger.info(f"ℹ️  {message}")


def log_debug(message: str):
    """Logga debug con emoji"""
    main_logger.debug(f"🔍 {message}")


if __name__ == "__main__":
    # Test logger
    print("Testing logger module...\n")

    # Test different log levels
    main_logger.debug("This is a DEBUG message")
    main_logger.info("This is an INFO message")
    main_logger.warning("This is a WARNING message")
    main_logger.error("This is an ERROR message")

    # Test emoji helpers
    log_success("Operation completed successfully")
    log_warning("This is a warning")
    log_error("This is an error")

    # Test startup info
    log_startup_info()

    print("\n✅ Logger test completed!")
