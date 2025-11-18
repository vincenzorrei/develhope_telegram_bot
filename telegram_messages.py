"""
Messaggi UI Telegram per Bot Educativo

Questo file contiene tutti i messaggi statici dell'interfaccia Telegram.
Separato da prompts.py che contiene solo i veri prompt LLM.

STUDENTI: Modificate questi messaggi per personalizzare l'interfaccia del bot!

Tips per modificare i messaggi:
1. Mantenete la formattazione (emoji, sezioni)
2. Non rimuovete placeholder {variabili} - sono necessari
3. Testate sempre su Telegram dopo le modifiche
"""


class TelegramMessages:
    """
    Classe centralizzata per tutti i messaggi UI del bot Telegram.

    Separata dai prompt LLM per chiarezza e manutenibilità.
    Gli studenti possono modificare questi messaggi per personalizzare l'interfaccia.
    """

    # =========================================
    # WELCOME MESSAGES
    # =========================================

    WELCOME_USER = """👋 Ciao! Sono un bot educativo AI con capacità RAG.

Posso aiutarti a:
📚 Rispondere domande sui documenti caricati dagli admin
🔍 Cercare informazioni sul web
🖼️ Analizzare immagini che mi invii
💬 Mantenere una conversazione contestuale

Invia un messaggio o una domanda per iniziare!

Comandi disponibili:
/help - Mostra tutti i comandi
/clear - Cancella cronologia conversazione
/voice_on - Attiva risposte vocali
/voice_off - Disattiva risposte vocali"""

    WELCOME_ADMIN = """👋 Ciao Admin! Sono il bot educativo AI con capacità RAG.

🔧 COMANDI ADMIN:
/add_doc - Carica nuovo documento (PDF, DOCX, TXT, MD)
/list_docs - Lista documenti caricati
/get_doc - Scarica documento originale per ID
/modify_summary - Modifica sommario documento
/delete_doc - Elimina documento per ID
/stats - Statistiche sistema (RAG, disk, users)
/memory_stats - Statistiche memoria (RAM, disk, evictions)

👤 COMANDI UTENTE:
/help - Mostra aiuto
/clear - Cancella cronologia
/voice_on - Attiva audio
/voice_off - Disattiva audio

Inizia caricando documenti con /add_doc oppure chiedimi qualcosa!"""

    # =========================================
    # HELP MESSAGES
    # =========================================

    HELP_MESSAGE_USER = """📖 GUIDA BOT EDUCATIVO

🎯 COSA POSSO FARE:
• Rispondere domande sui documenti caricati
• Cercare informazioni aggiornate sul web
• Analizzare immagini che mi invii
• Ricordare la nostra conversazione

💬 COMANDI DISPONIBILI:
/help - Mostra questo messaggio
/clear - Cancella cronologia conversazione
/voice_on - Attiva risposte vocali (TTS)
/voice_off - Disattiva risposte vocali

❓ COME USARMI:
1. Invia una domanda testuale
2. Oppure invia un'immagine con didascalia
3. Riceverai risposta basata su documenti, web o conoscenza generale

💡 TIPS:
• Sii specifico nelle domande per risposte migliori
• Puoi fare domande di follow-up sulla conversazione
• Le immagini vanno inviate come "documento" per qualità migliore"""

    HELP_MESSAGE_ADMIN = """📖 GUIDA BOT EDUCATIVO (ADMIN)

🔧 COMANDI AMMINISTRATIVI:
/add_doc - Inizia caricamento documento
  → Supporta: PDF, DOCX, TXT, MD
  → Max size: 20MB
  → Il bot processerà e indicizzerà il documento

/list_docs - Mostra tutti i documenti caricati
  → Vedi ID, nome, sommario, data caricamento, numero chunks

/get_doc <id> - Scarica documento originale
  → Esempio: /get_doc doc_12345
  → Ricevi il file fisico del documento caricato

/modify_summary <id> <nuovo_summary> - Modifica sommario
  → Esempio: /modify_summary doc_12345 Guida Python completa
  → Il sommario aiuta l'agent a decidere quando usare RAG

/delete_doc <id> - Elimina documento
  → Esempio: /delete_doc doc_12345
  → Elimina sia chunks che file fisico

/stats - Statistiche sistema
  → Documenti totali
  → Chunks indicizzati
  → Storage utilizzato
  → Utenti attivi

/memory_stats - Statistiche memoria conversazionale
  → Memoria RAM utilizzata
  → Users in cache
  → Disk usage e evictions

👤 COMANDI UTENTE:
/help - Mostra aiuto
/clear - Cancella cronologia
/voice_on - Attiva risposte audio
/voice_off - Disattiva risposte audio

🎓 GESTIONE DOCUMENTI:
1. Carica documenti con /add_doc
2. Verifica indicizzazione con /list_docs
3. Modifica sommario se necessario con /modify_summary
4. Scarica documenti originali con /get_doc
5. Gli utenti possono subito fare query RAG
6. Elimina documenti obsoleti con /delete_doc"""

    # =========================================
    # STATUS MESSAGES
    # =========================================

    NO_DOCUMENTS_FOUND = """📭 Nessun documento trovato nel database.

Gli admin devono caricare documenti prima che io possa rispondere a domande specifiche su materiale didattico.

Nel frattempo, posso:
• Rispondere a domande generali
• Cercare informazioni sul web
• Analizzare immagini

Cosa posso fare per te?"""

    DOCUMENT_ADDED_SUCCESS = """✅ Documento caricato con successo!

📄 Nome: {filename}
🔢 Chunks creati: {num_chunks}
🆔 ID documento: {doc_id}
📊 Total documenti: {total_docs}

Il documento è ora disponibile per query RAG!"""

    DOCUMENT_DELETED_SUCCESS = """✅ Documento eliminato con successo!

🗑️ ID: {doc_id}
📄 Nome: {filename}

Il documento è stato rimosso dal database vettoriale."""

    PROCESSING_DOCUMENT = """⏳ Sto processando il documento...

Operazioni in corso:
1. ✅ Download completato
2. 🔄 Estrazione testo in corso...
3. ⏳ Chunking...
4. ⏳ Generazione embeddings...
5. ⏳ Salvataggio in ChromaDB...

Questo può richiedere alcuni secondi per documenti grandi."""

    # =========================================
    # ERROR MESSAGES
    # =========================================

    ERROR_UNAUTHORIZED = """🚫 Accesso negato.

Questo comando è disponibile solo per gli amministratori.

Usa /help per vedere i comandi disponibili."""

    ERROR_FILE_TOO_LARGE = """❌ File troppo grande!

Max dimensione: {max_size_mb} MB
Dimensione file: {file_size_mb} MB

Riduci le dimensioni del file o dividilo in parti più piccole."""

    ERROR_UNSUPPORTED_FORMAT = """❌ Formato file non supportato.

Formati supportati:
• PDF (.pdf)
• Word (.docx)
• Testo (.txt)
• Markdown (.md)

Formato ricevuto: {file_format}"""

    ERROR_PROCESSING_DOCUMENT = """❌ Errore durante il processamento del documento.

Motivo: {error}

Riprova o contatta l'amministratore se il problema persiste."""

    ERROR_GENERIC = """❌ Si è verificato un errore.

{error_message}

Riprova o usa /help per assistenza."""

    # =========================================
    # VOICE MODE MESSAGES
    # =========================================

    VOICE_ENABLED = """🔊 Modalità vocale ATTIVATA!

Ora riceverai anche risposte audio (OpenAI TTS).

⚠️ Attenzione: TTS consuma più crediti API.

Disattiva con /voice_off"""

    VOICE_DISABLED = """🔇 Modalità vocale DISATTIVATA!

Riceverai solo risposte testuali.

Riattiva con /voice_on"""

    # =========================================
    # MEMORY MESSAGES
    # =========================================

    MEMORY_CLEARED = """✅ Memoria conversazione cancellata!

Possiamo ricominciare da zero. Come posso aiutarti?"""

    # =========================================
    # STATS MESSAGES
    # =========================================

    STATS_TEMPLATE = """📊 STATISTICHE SISTEMA

🗄️ DATABASE:
• Documenti totali: {total_docs}
• Chunks indicizzati: {total_chunks}
• Collection: {collection_name}

💾 STORAGE:
• VectorDB: {vectordb_size_mb} MB
• Documenti: {docs_size_mb} MB
• Totale: {total_size_mb} MB / {limit_mb} MB

👥 UTENTI:
• Utenti attivi: {active_users}
• Admin: {admin_count}

🤖 SISTEMA:
• LLM Model: {llm_model}
• Embedding Model: {embedding_model}
• RAG Top-K: {rag_top_k}"""


# =========================================
# EXPORTS
# =========================================
telegram_messages = TelegramMessages()


if __name__ == "__main__":
    # Test messages module
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    print("Testing telegram_messages module...")
    print("\n=== WELCOME MESSAGE ===")
    print(telegram_messages.WELCOME_USER)
    print("\n=== STATS TEMPLATE ===")
    print(telegram_messages.STATS_TEMPLATE.format(
        total_docs=10,
        total_chunks=500,
        collection_name="develhope_docs",
        vectordb_size_mb=5.2,
        docs_size_mb=15.8,
        total_size_mb=21.0,
        limit_mb=500,
        active_users=25,
        admin_count=3,
        llm_model="gpt-4o-mini",
        embedding_model="text-embedding-3-small",
        rag_top_k=5
    ))
    print("\n✅ All messages loaded successfully!")
