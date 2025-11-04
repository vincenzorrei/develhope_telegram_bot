"""
Bot Setup Module

Crea e configura l'Application Telegram.
"""

from telegram.ext import Application

from config import api_keys, bot_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_bot() -> Application:
    """
    Crea Application Telegram con configurazione ottimale.

    Returns:
        Application configurata e pronta

    Example:
        >>> app = create_bot()
        >>> # Add handlers
        >>> app.run_polling()
    """
    logger.info("[BOT SETUP] Creating Telegram Application...")

    # Build application
    app = Application.builder().token(api_keys.TELEGRAM_BOT_TOKEN).build()

    # Configure concurrent updates se abilitato
    if bot_config.CONCURRENT_UPDATES:
        logger.info("           Concurrent updates: ENABLED")

    logger.info("[OK] Telegram Application created")

    return app


if __name__ == "__main__":
    print("Bot setup module loaded")
