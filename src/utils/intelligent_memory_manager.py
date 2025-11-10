"""
Intelligent Memory Manager Module

Sistema di memoria ibrido con:
- ConversationSummaryBufferMemory (auto-summarization)
- LRU eviction (gestione RAM efficiente)
- Persistenza JSON su disco
- Auto-cleanup conversazioni vecchie

ARCHITETTURA:
┌─────────────────────────────────────────┐
│  RAM (LRU Cache - max 100 users)       │
│  - ConversationSummaryBufferMemory      │
│  - Token limit: 1500                    │
│  - Auto-eviction quando pieno           │
└─────────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────────┐
│  DISK (Unlimited users)                 │
│  - JSON persistence                     │
│  - Auto-save ogni N messaggi            │
│  - Auto-cleanup >30 giorni              │
└─────────────────────────────────────────┘

STUDENTI: Questo modulo ottimizza uso RAM e disk space.
Sperimentate con parametri in config.py!
"""

import json
import os
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import OrderedDict
from pathlib import Path

from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

from config import paths_config, memory_config, llm_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class IntelligentMemoryManager:
    """
    Gestore intelligente memoria conversazionale con persistenza.

    Features:
    1. Auto-summarization quando supera token limit
    2. LRU eviction per gestione RAM (max users in cache)
    3. Persistenza su disco (JSON)
    4. Auto-save periodico
    5. Cleanup automatico conversazioni vecchie

    Memory Strategy:
    - Recent messages: Mantieni ultimi ~500 tokens intatti (dettagli)
    - Old messages: Riassumi in summary cumulativo (~300 tokens)
    - Total per user: ~800 tokens (vs illimitato con ConversationBufferMemory)

    Example:
        >>> manager = IntelligentMemoryManager()
        >>> memory = manager.get_memory(user_id=123)
        >>> manager.save_interaction(123, "Ciao", "Ciao! Come posso aiutarti?")
        >>> stats = manager.get_stats()
    """

    def __init__(self):
        """
        Inizializza IntelligentMemoryManager.

        STUDENTI: Questo manager ottimizza automaticamente memoria!
        Parametri configurabili in config.py (MemoryConfig).
        """
        # Configurazione da config.py
        self.conversations_dir = paths_config.CONVERSATIONS_DIR
        self.token_limit = memory_config.TOKEN_LIMIT
        self.save_interval = memory_config.SAVE_INTERVAL
        self.max_cached_users = memory_config.MAX_CACHED_USERS

        # LLM per summarization (usa modello veloce ed economico)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # Economico per summarization
            temperature=0  # Deterministico per summaries
        )

        # LRU cache: OrderedDict mantiene ordine di accesso
        self.user_memories: OrderedDict[int, ConversationSummaryBufferMemory] = OrderedDict()

        # Tracking ultimo accesso (per eviction)
        self.last_access: Dict[int, datetime] = {}

        # Message counters per user (per auto-save)
        self.message_counters: Dict[int, int] = {}

        # Statistics tracking
        self.summarization_count = 0
        self.eviction_count = 0

        # Crea directory se non esiste
        os.makedirs(self.conversations_dir, exist_ok=True)

        logger.info("🧠 [INIT] IntelligentMemoryManager")
        logger.info(f"       Directory: {self.conversations_dir}")
        logger.info(f"       Token limit: {self.token_limit}")
        logger.info(f"       Max cached users: {self.max_cached_users}")
        logger.info(f"       Save interval: {self.save_interval} messages")

    # ========================================
    # CORE MEMORY OPERATIONS
    # ========================================

    def get_memory(self, user_id: int) -> ConversationSummaryBufferMemory:
        """
        Ottieni memoria per user_id (crea se non esiste).

        Workflow:
        1. Update last_access timestamp
        2. Evict utenti inattivi se RAM piena (>max_cached_users)
        3. Load da disco o crea nuova memoria
        4. Return memoria

        Args:
            user_id: Telegram user ID

        Returns:
            ConversationSummaryBufferMemory per l'utente

        Example:
            >>> memory = manager.get_memory(123)
            >>> memory.save_context({"input": "Hi"}, {"output": "Hello!"})
        """
        # Update ultimo accesso (per LRU)
        self.last_access[user_id] = datetime.now()

        # Evict se troppi utenti in RAM
        if len(self.user_memories) >= self.max_cached_users and user_id not in self.user_memories:
            self._evict_oldest_user()

        # Load o crea memoria
        if user_id not in self.user_memories:
            # Try load da disco
            loaded_memory = self._load_from_disk(user_id)

            if loaded_memory:
                self.user_memories[user_id] = loaded_memory
                logger.debug(f"[LOAD] Memory restored from disk for user {user_id}")
            else:
                # Crea nuova memoria
                self.user_memories[user_id] = self._create_new_memory()
                logger.debug(f"[CREATE] New memory for user {user_id}")

            # Move to end (most recently used)
            self.user_memories.move_to_end(user_id)

        return self.user_memories[user_id]

    def save_interaction(
        self,
        user_id: int,
        user_message: str,
        ai_response: str
    ):
        """
        Salva interazione nella memoria utente.

        Features:
        - Auto-save su disco ogni N messaggi (configurabile)
        - Tracking message count per user

        Args:
            user_id: Telegram user ID
            user_message: Messaggio utente
            ai_response: Risposta bot

        Example:
            >>> manager.save_interaction(123, "Ciao", "Ciao! Come posso aiutarti?")
        """
        memory = self.get_memory(user_id)

        # Salva nel memory buffer
        memory.save_context(
            {"input": user_message},
            {"output": ai_response}
        )

        # Increment message counter
        self.message_counters[user_id] = self.message_counters.get(user_id, 0) + 1

        # Auto-save periodico su disco
        if self.message_counters[user_id] % self.save_interval == 0:
            self._save_to_disk(user_id)
            logger.debug(f"[AUTO-SAVE] User {user_id} - {self.message_counters[user_id]} messages")

    def clear_memory(self, user_id: int):
        """
        Pulisce memoria utente (comando /clear).

        Args:
            user_id: Telegram user ID
        """
        if user_id in self.user_memories:
            # Crea memoria pulita
            self.user_memories[user_id] = self._create_new_memory()

            # Delete file da disco
            self._delete_from_disk(user_id)

            # Reset counter
            self.message_counters[user_id] = 0

            logger.info(f"[CLEAR] Memory cleared for user {user_id}")

    # ========================================
    # DISK PERSISTENCE
    # ========================================

    def _save_to_disk(self, user_id: int):
        """
        Salva memoria utente su disco (JSON).

        Format JSON:
        {
            "user_id": 123,
            "summary": "Summary of old messages...",
            "messages": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ],
            "last_access": "2025-01-06T15:30:00"
        }

        Args:
            user_id: Telegram user ID
        """
        memory = self.user_memories.get(user_id)
        if not memory:
            return

        try:
            # Estrai dati da memoria
            messages_data = []
            for msg in memory.chat_memory.messages:
                if isinstance(msg, HumanMessage):
                    role = "user"
                elif isinstance(msg, AIMessage):
                    role = "assistant"
                else:
                    role = "system"

                # Converti content a stringa (potrebbe essere vari tipi)
                content = str(msg.content) if hasattr(msg, 'content') else ""

                messages_data.append({
                    "role": role,
                    "content": content
                })

            # Estrai summary (può essere str, list, o None)
            summary = ""
            if hasattr(memory, 'buffer'):
                if isinstance(memory.buffer, str):
                    summary = memory.buffer
                elif isinstance(memory.buffer, list):
                    # Se è una lista di messaggi, concatena i content
                    summary = "\n".join(
                        str(item.content) if hasattr(item, 'content') else str(item)
                        for item in memory.buffer
                    )

            # Costruisci JSON
            data = {
                "user_id": user_id,
                "summary": summary,
                "messages": messages_data,
                "last_access": datetime.now().isoformat(),
                "message_count": len(messages_data)
            }

            # Salva su disco
            filepath = self._get_filepath(user_id)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"[SAVE] User {user_id} → {filepath}")

        except Exception as e:
            logger.error(f"[ERROR] Failed to save user {user_id}: {e}")

    def _load_from_disk(self, user_id: int) -> Optional[ConversationSummaryBufferMemory]:
        """
        Carica memoria utente da disco.

        Args:
            user_id: Telegram user ID

        Returns:
            ConversationSummaryBufferMemory o None se non esiste
        """
        filepath = self._get_filepath(user_id)

        if not os.path.exists(filepath):
            return None

        try:
            # Leggi JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Crea nuova memoria
            memory = self._create_new_memory()

            # Restore summary
            if 'summary' in data and data['summary']:
                memory.buffer = data['summary']

            # Restore messages
            for msg_data in data.get('messages', []):
                if msg_data['role'] == 'user':
                    memory.chat_memory.add_message(HumanMessage(content=msg_data['content']))
                elif msg_data['role'] == 'assistant':
                    memory.chat_memory.add_message(AIMessage(content=msg_data['content']))

            logger.debug(f"[LOAD] User {user_id} ← {filepath}")
            return memory

        except Exception as e:
            logger.error(f"[ERROR] Failed to load user {user_id}: {e}")
            return None

    def _delete_from_disk(self, user_id: int):
        """Elimina file conversazione da disco."""
        filepath = self._get_filepath(user_id)
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"[DELETE] Removed {filepath}")

    def _get_filepath(self, user_id: int) -> str:
        """Get filepath per user conversation."""
        return os.path.join(self.conversations_dir, f"user_{user_id}.json")

    # ========================================
    # LRU EVICTION & CLEANUP
    # ========================================

    def _evict_oldest_user(self):
        """
        Evict utente meno recente da RAM (LRU strategy).

        Steps:
        1. Trova utente con oldest last_access
        2. Salva su disco
        3. Rimuovi da RAM

        STUDENTI: Questo permette scalare a 1000+ utenti
        mantenendo solo 100 in RAM!
        """
        if not self.user_memories:
            return

        # Trova utente meno recente
        oldest_user = min(self.last_access, key=self.last_access.get)

        # Salva prima di evict
        self._save_to_disk(oldest_user)

        # Rimuovi da RAM
        del self.user_memories[oldest_user]
        del self.last_access[oldest_user]
        if oldest_user in self.message_counters:
            del self.message_counters[oldest_user]

        self.eviction_count += 1
        logger.info(f"[EVICT] User {oldest_user} evicted from RAM (LRU)")

    def cleanup_old_conversations(self, days: int = 30):
        """
        Elimina conversazioni inattive da disco.

        PRIVACY & DISK MANAGEMENT:
        - GDPR compliance: rimuovi dati vecchi
        - Previeni disk overflow

        Args:
            days: Elimina conversazioni > N giorni (default: 30)

        Example:
            >>> manager.cleanup_old_conversations(days=30)
            [CLEANUP] Deleted 5 old conversations
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        logger.info(f"[CLEANUP] Starting cleanup (cutoff: {days} days)...")

        try:
            for filepath in Path(self.conversations_dir).glob("user_*.json"):
                try:
                    # Check file modification time
                    file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime)

                    # Delete se troppo vecchio
                    if file_mtime < cutoff_date:
                        filepath.unlink()
                        deleted_count += 1
                        logger.debug(f"[CLEANUP] Deleted: {filepath.name}")

                except Exception as e:
                    logger.warning(f"[CLEANUP] Error processing {filepath.name}: {e}")

            logger.info(f"[CLEANUP] Completed - Deleted {deleted_count} old conversations")
            return deleted_count

        except Exception as e:
            logger.error(f"[CLEANUP] Failed: {e}")
            return 0

    # ========================================
    # HELPER METHODS
    # ========================================

    def _create_new_memory(self) -> ConversationSummaryBufferMemory:
        """
        Crea nuova ConversationSummaryBufferMemory.

        STUDENTI: Questo usa il tipo di memoria ibrido!
        - Mantiene recent messages intatti (dettagli)
        - Riassume old messages automaticamente (long-term context)

        Returns:
            Nuova memoria configurata
        """
        return ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=self.token_limit,
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )

    # ========================================
    # STATISTICS & MONITORING
    # ========================================

    def get_stats(self) -> Dict:
        """
        Ottieni statistiche uso memoria.

        Returns:
            Dict con metriche:
            - users_in_ram: Utenti caricati in RAM
            - total_users: Totale utenti su disco
            - estimated_tokens: Stima token in RAM
            - estimated_ram_mb: Stima RAM usage (MB)
            - disk_usage_mb: Spazio disco usato (MB)
            - summarizations_count: Numero summarizations eseguite
            - evictions_count: Numero evictions da RAM

        Example:
            >>> stats = manager.get_stats()
            >>> print(f"RAM: {stats['estimated_ram_mb']:.2f} MB")
        """
        try:
            # Count users
            users_in_ram = len(self.user_memories)

            # Count file su disco
            disk_files = list(Path(self.conversations_dir).glob("user_*.json"))
            total_users = len(disk_files)

            # Stima tokens in RAM
            total_tokens = 0
            for memory in self.user_memories.values():
                # Count tokens in buffer (summary)
                if hasattr(memory, 'buffer') and memory.buffer:
                    # Buffer può essere str o list
                    if isinstance(memory.buffer, str):
                        total_tokens += len(memory.buffer.split())
                    elif isinstance(memory.buffer, list):
                        for item in memory.buffer:
                            if hasattr(item, 'content'):
                                total_tokens += len(str(item.content).split())

                # Count tokens in messages
                for msg in memory.chat_memory.messages:
                    if hasattr(msg, 'content'):
                        total_tokens += len(str(msg.content).split())

            # Stima RAM (approssimativo: ~4 bytes per token)
            estimated_ram_mb = (total_tokens * 4) / (1024 * 1024)

            # Calcola disk usage
            disk_usage_bytes = sum(f.stat().st_size for f in disk_files)
            disk_usage_mb = disk_usage_bytes / (1024 * 1024)

            return {
                "users_in_ram": users_in_ram,
                "total_users": total_users,
                "estimated_tokens": total_tokens,
                "estimated_ram_mb": round(estimated_ram_mb, 2),
                "disk_usage_mb": round(disk_usage_mb, 2),
                "summarizations_count": self.summarization_count,
                "evictions_count": self.eviction_count,
                "max_cached_users": self.max_cached_users
            }

        except Exception as e:
            logger.error(f"[ERROR] Failed to get stats: {e}")
            return {
                "users_in_ram": len(self.user_memories),
                "total_users": 0,
                "estimated_tokens": 0,
                "estimated_ram_mb": 0.0,
                "disk_usage_mb": 0.0,
                "summarizations_count": self.summarization_count,
                "evictions_count": self.eviction_count,
                "max_cached_users": self.max_cached_users
            }

    def force_save_all(self):
        """
        Forza salvataggio di tutti gli utenti in RAM su disco.

        Utile prima di shutdown del bot.

        Example:
            >>> manager.force_save_all()
            [FORCE-SAVE] Saved 25 users to disk
        """
        logger.info("[FORCE-SAVE] Saving all users to disk...")
        saved_count = 0

        for user_id in list(self.user_memories.keys()):
            try:
                self._save_to_disk(user_id)
                saved_count += 1
            except Exception as e:
                logger.error(f"[FORCE-SAVE] Failed to save user {user_id}: {e}")

        logger.info(f"[FORCE-SAVE] Saved {saved_count} users to disk")
        return saved_count


if __name__ == "__main__":
    # Test IntelligentMemoryManager
    print("Testing IntelligentMemoryManager...\n")

    try:
        # Initialize
        manager = IntelligentMemoryManager()
        print(f"[OK] Manager initialized")
        print(f"     Token limit: {manager.token_limit}")
        print(f"     Max cached users: {manager.max_cached_users}")

        # Test memoria creation
        memory = manager.get_memory(user_id=123)
        print(f"\n[OK] Memory created for user 123")

        # Test save interaction
        manager.save_interaction(123, "Ciao", "Ciao! Come posso aiutarti?")
        manager.save_interaction(123, "Come stai?", "Bene, grazie!")
        print(f"[OK] Interactions saved")

        # Test stats
        stats = manager.get_stats()
        print(f"\n[OK] Stats:")
        for key, value in stats.items():
            print(f"     {key}: {value}")

        # Test disk persistence
        manager._save_to_disk(123)
        print(f"\n[OK] Saved to disk")

        # Test cleanup (dry run - 0 days)
        deleted = manager.cleanup_old_conversations(days=999)
        print(f"\n[OK] Cleanup test: {deleted} files deleted")

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
