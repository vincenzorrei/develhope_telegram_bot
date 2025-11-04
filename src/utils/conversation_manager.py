"""
Conversation Manager Module

Gestisce memoria conversazionale persistente per utenti.
Salva/carica cronologie conversazioni su disco.

OPZIONALE: Questo modulo è per persistenza avanzata.
Il bot funziona anche senza questo (usa solo memoria RAM).
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from config import paths_config, memory_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationManager:
    """
    Gestore conversazioni con persistenza su disco.

    Features:
    1. Salva cronologie su JSON
    2. Carica all'avvio bot
    3. Auto-save periodico
    4. Cleanup conversazioni vecchie

    Example:
        >>> manager = ConversationManager()
        >>> manager.save_conversation(user_id=123, messages=[...])
        >>> messages = manager.load_conversation(user_id=123)
    """

    def __init__(self):
        """Inizializza ConversationManager."""
        self.conversations_dir = paths_config.CONVERSATIONS_DIR
        self.save_interval = memory_config.SAVE_INTERVAL

        # Crea directory se non esiste
        os.makedirs(self.conversations_dir, exist_ok=True)

        logger.info("[INIT] ConversationManager")
        logger.info(f"       Directory: {self.conversations_dir}")

    def _get_filepath(self, user_id: int) -> str:
        """Get filepath per user conversation."""
        return os.path.join(
            self.conversations_dir,
            f"user_{user_id}.json"
        )

    def save_conversation(
        self,
        user_id: int,
        messages: List[Dict]
    ):
        """
        Salva conversazione su disco.

        Args:
            user_id: Telegram user ID
            messages: Lista messaggi in format:
                     [{"role": "user/assistant", "content": "text"}, ...]
        """
        filepath = self._get_filepath(user_id)

        data = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "messages": messages
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"[SAVE] Conversation for user {user_id}")

        except Exception as e:
            logger.error(f"[ERROR] Failed to save conversation: {e}")

    def load_conversation(self, user_id: int) -> Optional[List[Dict]]:
        """
        Carica conversazione da disco.

        Args:
            user_id: Telegram user ID

        Returns:
            Lista messaggi o None
        """
        filepath = self._get_filepath(user_id)

        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.debug(f"[LOAD] Conversation for user {user_id}")
            return data.get('messages', [])

        except Exception as e:
            logger.error(f"[ERROR] Failed to load conversation: {e}")
            return None

    def delete_conversation(self, user_id: int):
        """Elimina conversazione salvata."""
        filepath = self._get_filepath(user_id)

        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"[DELETE] Conversation for user {user_id}")


if __name__ == "__main__":
    print("Conversation manager module loaded")
