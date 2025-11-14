"""
Telegram Handlers Module

Tutti gli handler per comandi e messaggi del bot.
Separati in: Admin handlers, User handlers, Message handlers.

IMPORTANTE:
- Tutti gli handler DEVONO essere async def
- Usare decoratori @admin_only o @user_or_admin
"""

import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from config import admin_config, bot_config, memory_config
from prompts import prompts
from telegram_messages import telegram_messages
from src.telegram.auth import admin_only, user_or_admin
from src.utils.logger import get_logger
from src.utils.helpers import (
    extract_file_extension,
    is_supported_document,
    format_file_size,
    get_directory_size_mb
)

logger = get_logger(__name__)


# ========================================
# HELPER FUNCTIONS
# ========================================

def format_error_message(error: Exception, context: str = "") -> str:
    """
    Formatta messaggio di errore in modo standardizzato.

    Args:
        error: Eccezione da formattare
        context: Contesto opzionale (es: "recupero documenti")

    Returns:
        Messaggio di errore formattato
    """
    if context:
        return f"❌ Errore {context}: {str(error)[:200]}"
    return f"❌ Errore: {str(error)[:200]}"


# ========================================
# ADMIN HANDLERS
# ========================================

@admin_only
async def add_doc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /add_doc - Inizia flow caricamento documento.

    Admin only. Avvia processo upload documento.
    """
    await update.message.reply_text(
        "Invia il documento che vuoi caricare.\n\n"
        "Formati supportati:\n"
        "- PDF (.pdf)\n"
        "- Word (.docx)\n"
        "- Testo (.txt)\n"
        "- Markdown (.md)\n\n"
        "Max dimensione: 20MB"
    )


@admin_only
async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler per documenti ricevuti.

    Processa documento:
    1. Download
    2. Validazione
    3. Processing con DocumentProcessor
    4. Add to VectorStore
    """
    document = update.message.document

    if not document:
        await update.message.reply_text("❌ Errore: Nessun documento ricevuto.")
        return

    filename = document.file_name
    file_size = document.file_size

    logger.info(f"[DOC] Received: {filename} ({format_file_size(file_size)})")

    # ========================================
    # Validazione
    # ========================================

    # Check formato supportato
    if not is_supported_document(filename):
        file_ext = extract_file_extension(filename)
        await update.message.reply_text(
            telegram_messages.ERROR_UNSUPPORTED_FORMAT.format(file_format=file_ext)
        )
        return

    # Check dimensione
    if file_size > bot_config.MAX_FILE_SIZE_BYTES:
        await update.message.reply_text(
            telegram_messages.ERROR_FILE_TOO_LARGE.format(
                max_size_mb=bot_config.MAX_FILE_SIZE_MB,
                file_size_mb=round(file_size / (1024*1024), 2)
            )
        )
        return

    # ========================================
    # Processing
    # ========================================

    await update.message.reply_text(telegram_messages.PROCESSING_DOCUMENT)

    try:
        # Download file
        file = await document.get_file()

        # Temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp_file:
            await file.download_to_drive(tmp_file.name)
            tmp_filepath = tmp_file.name

        # Get components from context
        document_processor = context.bot_data['document_processor']
        vector_store = context.bot_data['vector_store']

        # Process and add to vector store
        doc_id, num_chunks, summary = document_processor.process_and_add(
            filepath=tmp_filepath,
            filename=filename,
            vector_store=vector_store
        )

        # Cleanup temp file
        os.remove(tmp_filepath)

        # Get stats
        stats = vector_store.get_stats()

        # Success message con sommario
        success_message = telegram_messages.DOCUMENT_ADDED_SUCCESS.format(
            filename=filename,
            num_chunks=num_chunks,
            doc_id=doc_id,
            total_docs=stats['total_documents']
        )
        success_message += f"\n<b>Sommario:</b> <i>{summary}</i>"

        await update.message.reply_text(success_message, parse_mode='HTML')

        logger.info(f"[SUCCESS] Document added: {doc_id}")

        # ========================================
        # REFRESH AGENT: Aggiorna tool descriptions e system prompt
        # ========================================
        # Dopo l'aggiunta di un nuovo documento, ricrea l'agent per
        # assicurare che le tool descriptions includano il nuovo documento
        langchain_engine = context.bot_data.get('langchain_engine')
        if langchain_engine:
            langchain_engine.refresh_agent()
            logger.info("[REFRESH] Agent refreshed after document addition")

    except Exception as e:
        logger.error(f"[ERROR] Document processing failed: {e}")
        import traceback
        traceback.print_exc()

        await update.message.reply_text(
            telegram_messages.ERROR_PROCESSING_DOCUMENT.format(error=str(e)[:200])
        )


@admin_only
async def list_docs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /list_docs - Lista tutti i documenti caricati.

    Admin only.
    """
    vector_store = context.bot_data['vector_store']

    try:
        documents = vector_store.list_all_documents()

        if not documents:
            await update.message.reply_text(telegram_messages.NO_DOCUMENTS_FOUND)
            return

        # Format list usando HTML invece di Markdown per evitare problemi con caratteri speciali
        message = f"<b>Documenti caricati ({len(documents)}):</b>\n\n"

        for i, doc in enumerate(documents, 1):
            message += f"{i}. <b>{doc['source']}</b>\n"
            message += f"   <i>{doc.get('summary', 'No summary')}</i>\n"
            message += f"   ID: <code>{doc['doc_id']}</code>\n"
            message += f"   Chunks: {doc['num_chunks']}\n"
            message += f"   Data: {doc['timestamp'][:10]}\n\n"

        await update.message.reply_text(message, parse_mode='HTML')

    except Exception as e:
        logger.error(f"[ERROR] List docs failed: {e}")
        # Usa formato standardizzato per errori
        await update.message.reply_text(format_error_message(e, "nel recupero dei documenti"))


@admin_only
async def delete_doc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /delete_doc <doc_id> - Elimina documento.

    Admin only. Usage: /delete_doc doc_123456

    Elimina:
    1. Tutti i chunks dal vector store
    2. File fisico dalla cartella data/documents/
    """
    if not context.args:
        await update.message.reply_text(
            "Usage: /delete_doc <doc_id>\n\n"
            "Usa /list_docs per vedere gli ID documenti."
        )
        return

    doc_id = context.args[0]
    vector_store = context.bot_data['vector_store']

    try:
        # Get info before delete
        doc_info = vector_store.get_document_info(doc_id)

        if not doc_info:
            await update.message.reply_text(f"Documento '{doc_id}' non trovato.")
            return

        # ========================================
        # Step 1: Delete from vector store
        # ========================================
        num_deleted = vector_store.delete_document(doc_id)

        # ========================================
        # Step 2: Delete physical file from data/documents/
        # ========================================
        from config import paths_config
        from pathlib import Path

        documents_dir = Path(paths_config.DOCUMENTS_DIR)
        deleted_files = []

        # Find and delete all files starting with doc_id_
        for filepath in documents_dir.glob(f"{doc_id}_*"):
            try:
                filepath.unlink()  # Delete file
                deleted_files.append(filepath.name)
                logger.info(f"[DELETE] Removed physical file: {filepath.name}")
            except Exception as e:
                logger.warning(f"[WARN] Could not delete file {filepath.name}: {e}")

        # Success message
        message = telegram_messages.DOCUMENT_DELETED_SUCCESS.format(
            doc_id=doc_id,
            filename=doc_info['source']
        )

        if deleted_files:
            message += f"\n\nFile eliminato: <code>{deleted_files[0]}</code>"

        await update.message.reply_text(message, parse_mode='HTML')

        logger.info(f"[DELETE] Document {doc_id} ({num_deleted} chunks, {len(deleted_files)} files)")

        # ========================================
        # REFRESH AGENT: Aggiorna tool descriptions e system prompt
        # ========================================
        # Dopo l'eliminazione di un documento, ricrea l'agent per
        # assicurare che le tool descriptions riflettano i documenti attuali
        langchain_engine = context.bot_data.get('langchain_engine')
        if langchain_engine:
            langchain_engine.refresh_agent()
            logger.info("[REFRESH] Agent refreshed after document deletion")

    except Exception as e:
        logger.error(f"[ERROR] Delete doc failed: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(format_error_message(e))


@admin_only
async def get_doc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /get_doc <doc_id> - Scarica il documento originale.

    Admin only. Usage: /get_doc doc_123456

    Invia il file fisico del documento all'admin.
    """
    if not context.args:
        await update.message.reply_text(
            "Usage: /get_doc <doc_id>\n\n"
            "Usa /list_docs per vedere gli ID documenti."
        )
        return

    doc_id = context.args[0]
    vector_store = context.bot_data['vector_store']

    try:
        # Verifica che il documento esista nel vector store
        doc_info = vector_store.get_document_info(doc_id)

        if not doc_info:
            await update.message.reply_text(f"Documento '{doc_id}' non trovato.")
            return

        # ========================================
        # Find physical file in data/documents/
        # ========================================
        from config import paths_config
        from pathlib import Path

        documents_dir = Path(paths_config.DOCUMENTS_DIR)

        # Find file starting with doc_id_
        matching_files = list(documents_dir.glob(f"{doc_id}_*"))

        if not matching_files:
            await update.message.reply_text(
                f"⚠️ Documento '{doc_id}' trovato nel database ma file fisico non presente.\n\n"
                f"Nome originale: <code>{doc_info['source']}</code>",
                parse_mode='HTML'
            )
            logger.warning(f"[GET_DOC] File not found for {doc_id}")
            return

        # Get first matching file
        filepath = matching_files[0]

        logger.info(f"[GET_DOC] Sending document: {filepath.name}")

        # ========================================
        # Send document to admin
        # ========================================
        await update.message.reply_text("📤 Invio documento...")

        with open(filepath, 'rb') as doc_file:
            await update.message.reply_document(
                document=doc_file,
                filename=doc_info['source'],  # Use original filename
                caption=f"📄 Documento: <b>{doc_info['source']}</b>\n"
                        f"ID: <code>{doc_id}</code>\n"
                        f"Chunks: {doc_info['num_chunks']}\n"
                        f"Data: {doc_info['timestamp'][:10]}",
                parse_mode='HTML'
            )

        logger.info(f"[GET_DOC] Document sent successfully: {doc_id}")

    except Exception as e:
        logger.error(f"[ERROR] Get doc failed: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f"Errore: {str(e)}")


@admin_only
async def modify_summary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /modify_summary <doc_id> <nuovo_summary> - Modifica il sommario di un documento.

    Admin only. Usage: /modify_summary doc_123456 Nuovo sommario del documento

    Il sommario viene visualizzato in /list_docs e aiuta l'agent a decidere
    quando usare il RAG tool per le query.
    """
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /modify_summary <doc_id> <nuovo_summary>\n\n"
            "Esempio:\n"
            "<code>/modify_summary doc_12345 Guida Python - variabili, funzioni, classi</code>\n\n"
            "Usa /list_docs per vedere gli ID documenti.",
            parse_mode='HTML'
        )
        return

    doc_id = context.args[0]
    # Join all remaining args as the new summary
    new_summary = " ".join(context.args[1:])

    vector_store = context.bot_data['vector_store']

    try:
        # Verifica che il documento esista
        doc_info = vector_store.get_document_info(doc_id)

        if not doc_info:
            await update.message.reply_text(f"Documento '{doc_id}' non trovato.")
            return

        # Show current summary
        old_summary = doc_info.get('summary', 'No summary')

        await update.message.reply_text(
            f"🔄 Aggiornamento sommario per: <b>{doc_info['source']}</b>\n\n"
            f"<b>Sommario attuale:</b>\n<i>{old_summary}</i>\n\n"
            f"<b>Nuovo sommario:</b>\n<i>{new_summary}</i>\n\n"
            f"Aggiornamento in corso...",
            parse_mode='HTML'
        )

        # ========================================
        # Update summary in vector store
        # ========================================
        num_updated = vector_store.update_document_summary(doc_id, new_summary)

        await update.message.reply_text(
            f"✅ Sommario aggiornato con successo!\n\n"
            f"📄 Documento: <b>{doc_info['source']}</b>\n"
            f"🆔 ID: <code>{doc_id}</code>\n"
            f"🔢 Chunks aggiornati: {num_updated}\n\n"
            f"<b>Nuovo sommario:</b>\n<i>{new_summary}</i>",
            parse_mode='HTML'
        )

        logger.info(f"[MODIFY_SUMMARY] Updated summary for {doc_id} ({num_updated} chunks)")

        # ========================================
        # REFRESH AGENT: Aggiorna tool descriptions e system prompt
        # ========================================
        # Dopo la modifica del sommario, ricrea l'agent per
        # assicurare che le tool descriptions riflettano i sommari aggiornati
        langchain_engine = context.bot_data.get('langchain_engine')
        if langchain_engine:
            langchain_engine.refresh_agent()
            logger.info("[REFRESH] Agent refreshed after summary modification")

    except Exception as e:
        logger.error(f"[ERROR] Modify summary failed: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f"Errore: {str(e)}")


@admin_only
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /stats - Mostra statistiche sistema.

    Admin only.
    """
    vector_store = context.bot_data['vector_store']

    try:
        stats = vector_store.get_stats()

        # Calculate storage
        docs_size_mb = get_directory_size_mb("./data/documents")
        total_size_mb = stats['storage_size_mb'] + docs_size_mb

        # Calculate active users from session store
        langchain_engine = context.bot_data.get('langchain_engine')
        active_users_count = 0
        if langchain_engine and hasattr(langchain_engine, 'session_store'):
            active_users_count = len(langchain_engine.session_store)

        message = telegram_messages.STATS_TEMPLATE.format(
            total_docs=stats['total_documents'],
            total_chunks=stats['total_chunks'],
            collection_name=stats['collection_name'],
            vectordb_size_mb=stats['storage_size_mb'],
            docs_size_mb=round(docs_size_mb, 2),
            total_size_mb=round(total_size_mb, 2),
            limit_mb=2000,
            active_users=active_users_count,
            admin_count=len(admin_config.ADMIN_USER_IDS),
            llm_model=context.bot_data.get('llm_model', 'N/A'),
            embedding_model=context.bot_data.get('embedding_model', 'N/A'),
            rag_top_k=context.bot_data.get('rag_top_k', 'N/A')
        )

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"[ERROR] Stats failed: {e}")
        await update.message.reply_text(f"Errore: {str(e)}")


@admin_only
async def memory_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /memory_stats - Mostra statistiche memoria conversazionale.

    Visualizza:
    - Users in RAM / Total users
    - RAM usage stimato (MB)
    - Disk usage (MB)
    - Summarizations count
    - Evictions count

    Admin only.
    """
    langchain_engine = context.bot_data.get('langchain_engine')

    if not langchain_engine:
        await update.message.reply_text("⚠️ Engine non inizializzato")
        return

    try:
        # Get stats da session store
        session_store = langchain_engine.session_store
        total_users = len(session_store)

        # Calculate total messages and estimate RAM
        total_messages = 0
        estimated_tokens = 0

        for user_id, history in session_store.items():
            msg_count = len(history.messages)
            total_messages += msg_count
            # Stima 150 token per messaggio
            estimated_tokens += msg_count * 150

        # Stima RAM (1 token ≈ 4 bytes)
        estimated_ram_mb = (estimated_tokens * 4) / (1024 * 1024)

        # Format message
        message = f"""📊 **Statistiche Memoria Conversazionale**

👥 **Utenti**
   • Utenti attivi: {total_users}
   • Messaggi totali: {total_messages}
   • Media msg/utente: {total_messages / total_users if total_users > 0 else 0:.1f}

💾 **Memory Usage**
   • Tokens stimati: {estimated_tokens:,}
   • RAM stimata: {estimated_ram_mb:.2f} MB

⚙️ **Configuration**
   • Summary buffer threshold: {memory_config.MAX_TOKENS_BEFORE_SUMMARY} tokens
   • Recent messages kept: {memory_config.RECENT_MESSAGES_TO_KEEP}
   • Summary model: {memory_config.SUMMARY_MODEL}

💡 **Status**
{'✅ Memoria sotto controllo' if estimated_ram_mb < 100 else '⚠️ Considera pulizia memoria per utenti inattivi'}
"""

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"[ERROR] Memory stats failed: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f"Errore: {str(e)}")


# ========================================
# USER HANDLERS
# ========================================

@user_or_admin
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start - Messaggio benvenuto.

    Diverso per admin vs utenti normali.
    """
    user = update.effective_user
    is_admin = admin_config.is_admin(user.id)

    if is_admin:
        message = telegram_messages.WELCOME_ADMIN
    else:
        message = telegram_messages.WELCOME_USER

    await update.message.reply_text(message)


@user_or_admin
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help - Mostra aiuto.

    Diverso per admin vs utenti.
    """
    user = update.effective_user
    is_admin = admin_config.is_admin(user.id)

    if is_admin:
        message = telegram_messages.HELP_MESSAGE_ADMIN
    else:
        message = telegram_messages.HELP_MESSAGE_USER

    await update.message.reply_text(message)


@user_or_admin
async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /clear - Cancella cronologia conversazione.
    """
    user_id = update.effective_user.id
    langchain_engine = context.bot_data['langchain_engine']

    langchain_engine.clear_memory(user_id)

    await update.message.reply_text(telegram_messages.MEMORY_CLEARED)


@user_or_admin
async def voice_on_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /voice_on - Attiva risposte vocali.
    """
    user_id = update.effective_user.id

    # Store in user_data
    context.user_data['voice_mode'] = True

    await update.message.reply_text(telegram_messages.VOICE_ENABLED)
    logger.info(f"[VOICE] Enabled for user {user_id}")


@user_or_admin
async def voice_off_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /voice_off - Disattiva risposte vocali.
    """
    user_id = update.effective_user.id

    context.user_data['voice_mode'] = False

    await update.message.reply_text(telegram_messages.VOICE_DISABLED)
    logger.info(f"[VOICE] Disabled for user {user_id}")


# ========================================
# MESSAGE HANDLERS
# ========================================

@user_or_admin
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler per messaggi testuali normali.

    Processa con LangChain + opzionale TTS.
    """
    user = update.effective_user
    user_id = user.id
    text = update.message.text

    logger.info(f"[MSG] User {user_id}: '{text[:50]}...'")

    # Show typing
    await update.message.chat.send_action(action="typing")

    try:
        message_processor = context.bot_data['message_processor']

        # Check voice mode
        voice_mode = context.user_data.get('voice_mode', False)

        # Process
        response, audio_bytes = await message_processor.process_text(
            text=text,
            user_id=user_id,
            generate_audio=voice_mode
        )

        # Send response based on voice mode
        if voice_mode and audio_bytes:
            # Voice mode: SOLO audio (no testo)
            await update.message.reply_voice(voice=audio_bytes)
        else:
            # Modalità normale: testo con formattazione HTML
            await update.message.reply_text(response, parse_mode='HTML')

    except Exception as e:
        logger.error(f"[ERROR] Message processing failed: {e}")
        import traceback
        traceback.print_exc()

        await update.message.reply_text(
            telegram_messages.ERROR_GENERIC.format(error_message=str(e)[:200])
        )


@user_or_admin
async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler per immagini.

    Analizza con GPT-4o Vision.
    """
    user_id = update.effective_user.id

    # Get largest photo
    photo = update.message.photo[-1]
    caption = update.message.caption

    logger.info(f"[IMAGE] User {user_id} sent image")

    await update.message.chat.send_action(action="typing")

    try:
        # Download image
        file = await photo.get_file()
        image_bytes = await file.download_as_bytearray()

        # Process
        message_processor = context.bot_data['message_processor']
        analysis = await message_processor.process_image(
            image_bytes=bytes(image_bytes),
            caption=caption,
            user_id=user_id
        )

        await update.message.reply_text(analysis, parse_mode='HTML')

    except Exception as e:
        logger.error(f"[ERROR] Image processing failed: {e}")
        await update.message.reply_text(f"Errore analisi immagine: {str(e)[:200]}")


@user_or_admin
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler per messaggi vocali.

    Trascrivi con Whisper e processa come testo normale.
    """
    user = update.effective_user
    user_id = user.id
    voice = update.message.voice

    logger.info(f"[VOICE] User {user_id} sent voice message ({voice.duration}s)")

    # Show typing
    await update.message.chat.send_action(action="typing")

    try:
        message_processor = context.bot_data['message_processor']

        # Download voice message
        file = await voice.get_file()
        audio_bytes = await file.download_as_bytearray()

        logger.info(f"[VOICE] Downloaded {len(audio_bytes)} bytes")

        # Trascrizione con Whisper
        transcribed_text = await message_processor.transcribe_audio(
            audio_bytes=bytes(audio_bytes),
            audio_format="ogg"  # Telegram voice messages are OGG
        )

        if not transcribed_text:
            await update.message.reply_text(
                "Non sono riuscito a trascrivere il messaggio vocale. "
                "Riprova parlando più chiaramente."
            )
            return

        logger.info(f"[VOICE] Transcription: '{transcribed_text}'")

        # Check voice mode per risposta
        voice_mode = context.user_data.get('voice_mode', False)

        # Process come messaggio testuale normale
        response, audio_bytes = await message_processor.process_text(
            text=transcribed_text,
            user_id=user_id,
            generate_audio=voice_mode
        )

        # Send response based on voice mode
        if voice_mode and audio_bytes:
            # Voice mode: SOLO audio
            await update.message.reply_voice(voice=audio_bytes)
        else:
            # Modalità normale: testo con formattazione HTML
            await update.message.reply_text(response, parse_mode='HTML')

    except Exception as e:
        logger.error(f"[ERROR] Voice processing failed: {e}")
        import traceback
        traceback.print_exc()

        await update.message.reply_text(
            f"Errore elaborazione messaggio vocale: {str(e)[:200]}"
        )


# ========================================
# SETUP FUNCTION
# ========================================

def setup_handlers(app, langchain_engine, vector_store, document_processor, message_processor, config_data):
    """
    Registra tutti gli handler nell'Application.

    Args:
        app: Telegram Application
        langchain_engine: LangChainEngine instance
        vector_store: VectorStoreManager instance
        document_processor: DocumentProcessor instance
        message_processor: MessageProcessor instance
        config_data: Dict con configurazioni
    """
    logger.info("[HANDLERS] Registering handlers...")

    # Store references in bot_data
    app.bot_data['langchain_engine'] = langchain_engine
    app.bot_data['vector_store'] = vector_store
    app.bot_data['document_processor'] = document_processor
    app.bot_data['message_processor'] = message_processor
    app.bot_data.update(config_data)

    # ========================================
    # Admin Command Handlers
    # ========================================
    app.add_handler(CommandHandler("add_doc", add_doc_handler))
    app.add_handler(CommandHandler("list_docs", list_docs_handler))
    app.add_handler(CommandHandler("delete_doc", delete_doc_handler))
    app.add_handler(CommandHandler("get_doc", get_doc_handler))
    app.add_handler(CommandHandler("modify_summary", modify_summary_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("memory_stats", memory_stats_handler))

    # ========================================
    # User Command Handlers
    # ========================================
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("clear", clear_handler))
    app.add_handler(CommandHandler("voice_on", voice_on_handler))
    app.add_handler(CommandHandler("voice_off", voice_off_handler))

    # ========================================
    # Message Handlers
    # ========================================
    # Document handler (per admin)
    app.add_handler(MessageHandler(
        filters.Document.ALL,
        document_handler
    ))

    # Image handler
    app.add_handler(MessageHandler(
        filters.PHOTO,
        image_handler
    ))

    # Voice message handler
    app.add_handler(MessageHandler(
        filters.VOICE,
        voice_handler
    ))

    # Text message handler (catch-all, deve essere ultimo!)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        message_handler
    ))

    logger.info("[OK] All handlers registered")
    logger.info("      Admin: 7 commands")
    logger.info("      User: 5 commands")
    logger.info("      Message: 4 types (text, voice, image, document)")


if __name__ == "__main__":
    print("Handlers module loaded")
