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

from config import admin_config, bot_config
from prompts import prompts
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
# ADMIN HANDLERS
# ========================================

@admin_only
async def add_doc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /add_doc - Inizia flow caricamento documento.

    Admin only. Avvia processo upload documento.
    """
    await update.message.reply_text(
        "Invia il documento (PDF, DOCX, o TXT) che vuoi caricare.\n\n"
        "Formati supportati:\n"
        "- PDF (.pdf)\n"
        "- Word (.docx)\n"
        "- Testo (.txt)\n\n"
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
        await update.message.reply_text("Errore: Nessun documento ricevuto.")
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
            prompts.ERROR_UNSUPPORTED_FORMAT.format(file_format=file_ext)
        )
        return

    # Check dimensione
    if file_size > bot_config.MAX_FILE_SIZE_BYTES:
        await update.message.reply_text(
            prompts.ERROR_FILE_TOO_LARGE.format(
                max_size_mb=bot_config.MAX_FILE_SIZE_MB,
                file_size_mb=round(file_size / (1024*1024), 2)
            )
        )
        return

    # ========================================
    # Processing
    # ========================================

    await update.message.reply_text(prompts.PROCESSING_DOCUMENT)

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
        doc_id, num_chunks = document_processor.process_and_add(
            filepath=tmp_filepath,
            filename=filename,
            vector_store=vector_store
        )

        # Cleanup temp file
        os.remove(tmp_filepath)

        # Get stats
        stats = vector_store.get_stats()

        # Success message
        await update.message.reply_text(
            prompts.DOCUMENT_ADDED_SUCCESS.format(
                filename=filename,
                num_chunks=num_chunks,
                doc_id=doc_id,
                total_docs=stats['total_documents']
            )
        )

        logger.info(f"[SUCCESS] Document added: {doc_id}")

    except Exception as e:
        logger.error(f"[ERROR] Document processing failed: {e}")
        import traceback
        traceback.print_exc()

        await update.message.reply_text(
            prompts.ERROR_PROCESSING_DOCUMENT.format(error=str(e)[:200])
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
            await update.message.reply_text(prompts.NO_DOCUMENTS_FOUND)
            return

        # Format list
        message = f"**Documenti caricati ({len(documents)}):**\n\n"

        for i, doc in enumerate(documents, 1):
            message += f"{i}. **{doc['source']}**\n"
            message += f"   ID: `{doc['doc_id']}`\n"
            message += f"   Chunks: {doc['num_chunks']}\n"
            message += f"   Data: {doc['timestamp'][:10]}\n\n"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"[ERROR] List docs failed: {e}")
        await update.message.reply_text(f"Errore: {str(e)}")


@admin_only
async def delete_doc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /delete_doc <doc_id> - Elimina documento.

    Admin only. Usage: /delete_doc doc_123456
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

        # Delete
        num_deleted = vector_store.delete_document(doc_id)

        await update.message.reply_text(
            prompts.DOCUMENT_DELETED_SUCCESS.format(
                doc_id=doc_id,
                filename=doc_info['source']
            )
        )

        logger.info(f"[DELETE] Document {doc_id} ({num_deleted} chunks)")

    except Exception as e:
        logger.error(f"[ERROR] Delete doc failed: {e}")
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

        message = prompts.STATS_TEMPLATE.format(
            total_docs=stats['total_documents'],
            total_chunks=stats['total_chunks'],
            collection_name=stats['collection_name'],
            vectordb_size_mb=stats['storage_size_mb'],
            docs_size_mb=round(docs_size_mb, 2),
            total_size_mb=round(total_size_mb, 2),
            limit_mb=2000,
            active_users=len(context.bot_data.get('langchain_engine', {}).user_memories or {}),
            admin_count=len(admin_config.ADMIN_USER_IDS),
            llm_model=context.bot_data.get('llm_model', 'N/A'),
            embedding_model=context.bot_data.get('embedding_model', 'N/A'),
            rag_top_k=context.bot_data.get('rag_top_k', 'N/A')
        )

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"[ERROR] Stats failed: {e}")
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
        message = prompts.WELCOME_ADMIN
    else:
        message = prompts.WELCOME_USER

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
        message = prompts.HELP_MESSAGE_ADMIN
    else:
        message = prompts.HELP_MESSAGE_USER

    await update.message.reply_text(message)


@user_or_admin
async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /clear - Cancella cronologia conversazione.
    """
    user_id = update.effective_user.id
    langchain_engine = context.bot_data['langchain_engine']

    langchain_engine.clear_memory(user_id)

    await update.message.reply_text(prompts.MEMORY_CLEARED)


@user_or_admin
async def voice_on_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /voice_on - Attiva risposte vocali.
    """
    user_id = update.effective_user.id

    # Store in user_data
    context.user_data['voice_mode'] = True

    await update.message.reply_text(prompts.VOICE_ENABLED)
    logger.info(f"[VOICE] Enabled for user {user_id}")


@user_or_admin
async def voice_off_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /voice_off - Disattiva risposte vocali.
    """
    user_id = update.effective_user.id

    context.user_data['voice_mode'] = False

    await update.message.reply_text(prompts.VOICE_DISABLED)
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

        # Send text response
        await update.message.reply_text(response)

        # Send audio if generated
        if audio_bytes:
            await update.message.reply_voice(voice=audio_bytes)

    except Exception as e:
        logger.error(f"[ERROR] Message processing failed: {e}")
        import traceback
        traceback.print_exc()

        await update.message.reply_text(
            prompts.ERROR_GENERIC.format(error_message=str(e)[:200])
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

        await update.message.reply_text(analysis)

    except Exception as e:
        logger.error(f"[ERROR] Image processing failed: {e}")
        await update.message.reply_text(f"Errore analisi immagine: {str(e)[:200]}")


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
    app.add_handler(CommandHandler("stats", stats_handler))

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

    # Text message handler (catch-all, deve essere ultimo!)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        message_handler
    ))

    logger.info("[OK] All handlers registered")
    logger.info("      Admin: 4 commands")
    logger.info("      User: 5 commands")
    logger.info("      Message: 3 types")


if __name__ == "__main__":
    print("Handlers module loaded")
