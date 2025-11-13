"""
Authentication Module

Decoratori per controllo accesso ai comandi Telegram.
Separa funzionalità admin da utenti normali.
"""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from config import admin_config
from telegram_messages import telegram_messages
from src.utils.logger import get_logger

logger = get_logger(__name__)


def admin_only(func):
    """
    Decorator per comandi solo admin.

    Verifica che user_id sia in ADMIN_USER_IDS.
    Se non autorizzato, invia messaggio di errore e blocca esecuzione.

    Usage:
        @admin_only
        async def add_doc_handler(update, context):
            # Solo admin possono eseguire questo

    Args:
        func: Handler function async

    Returns:
        Wrapped function con auth check
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id

        # Check se admin
        if not admin_config.is_admin(user_id):
            logger.warning(f"[AUTH] Unauthorized access attempt by user {user_id} (@{user.username})")

            await update.message.reply_text(telegram_messages.ERROR_UNAUTHORIZED)
            return

        # Admin autorizzato, esegui comando
        logger.info(f"[AUTH] Admin command executed by {user_id} (@{user.username})")
        return await func(update, context)

    return wrapper


def user_or_admin(func):
    """
    Decorator per comandi accessibili a tutti.

    Opzionale: puoi aggiungere whitelist se vuoi limitare
    l'accesso solo a utenti specifici + admin.

    Usage:
        @user_or_admin
        async def help_handler(update, context):
            # Tutti possono eseguire

    Args:
        func: Handler function async

    Returns:
        Wrapped function
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id

        logger.debug(f"[AUTH] User command by {user_id} (@{user.username})")

        # OPZIONALE: Implementa whitelist qui
        # if user_id not in ALLOWED_USER_IDS and not admin_config.is_admin(user_id):
        #     await update.message.reply_text("Non autorizzato")
        #     return

        return await func(update, context)

    return wrapper


if __name__ == "__main__":
    print("Auth decorators loaded successfully")
