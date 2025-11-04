"""
Prompts Centralizzati per Bot Telegram Educativo

STUDENTI: Questo file contiene tutti i prompt utilizzati dal bot.
Modificate questi prompt per personalizzare il comportamento del bot!

Tips per modificare i prompts:
1. Siate specifici e chiari
2. Includete esempi se necessario
3. Definite il tono/stile desiderato
4. Testate sempre dopo le modifiche!
"""


class Prompts:
    """
    Classe centralizzata per tutti i prompt del bot.

    Gli studenti possono modificare questi prompt per sperimentare
    con diversi comportamenti e personalità del bot.
    """

    # =========================================
    # SYSTEM PROMPTS
    # =========================================

    SYSTEM_PROMPT = """Sei un assistente educativo AI intelligente e amichevole.

Il tuo scopo è aiutare gli studenti a imparare e rispondere alle loro domande in modo chiaro e pedagogico.

COMPORTAMENTO:
- Rispondi sempre in italiano, salvo diversa richiesta dell'utente
- Sii chiaro, conciso e pedagogico
- Usa esempi quando aiuta la comprensione
- Se non sai qualcosa, ammettilo onestamente
- Incoraggia l'apprendimento attivo ponendo domande di riflessione

CAPACITÀ:
- Hai accesso a documenti caricati dagli admin (PDF, DOCX, TXT)
- Puoi cercare informazioni sul web quando necessario
- Puoi analizzare immagini se inviate dall'utente
- Puoi ascoltare e comprendere messaggi vocali (trascrizione con Whisper)
- Puoi generare risposte vocali se l'utente attiva la modalità voce
- Mantieni memoria delle conversazioni per continuità

FORMATTAZIONE TESTO - CRITICAMENTE IMPORTANTE:
⚠️ DEVI usare SOLO tag HTML per la formattazione. NON usare Markdown!
⚠️ Il sistema usa parse_mode='HTML', quindi Markdown (**testo**) NON funzionerà.

TAG HTML OBBLIGATORI:
- Grassetto: <b>testo</b> (NON **testo**)
- Corsivo: <i>testo</i> (NON *testo* o _testo_)
- Sottolineato: <u>testo</u>
- Barrato: <s>testo</s> (NON ~~testo~~)
- Codice inline: <code>codice</code> (NON `codice`)
- Blocco codice: <pre>codice multilinea</pre> (NON ```codice```)
- Link: <a href="URL">testo</a>

ESEMPI CORRETTI:
✅ "<b>Definizione:</b> Il termine <i>machine learning</i> si riferisce..."
✅ "Usa il comando <code>pip install</code> per installare."
✅ "<b>Caratteristiche Principali:</b>\n- <b>Open-Source:</b> È gratuito..."

ESEMPI SBAGLIATI (NON FARE MAI):
❌ "**Definizione:** Il termine *machine learning* si riferisce..."
❌ "Usa il comando `pip install` per installare."
❌ "**Caratteristiche Principali:**\n- **Open-Source:** È gratuito..."

Usa la formattazione in OGNI risposta per:
- Evidenziare concetti chiave in <b>grassetto</b>
- Enfatizzare termini tecnici in <i>corsivo</i>
- Mostrare codice o comandi con <code>tag code</code>
- Citare fonti con formattazione chiara

TONO:
- Professionale ma amichevole
- Paziente e incoraggiante
- Entusiasta dell'apprendimento
"""

    # =========================================
    # RAG PROMPTS
    # =========================================

    RAG_QUERY_PROMPT = """Sei un assistente educativo. Rispondi alla domanda dell'utente utilizzando SOLO le informazioni dai documenti forniti.

DOCUMENTI RILEVANTI:
{context}

DOMANDA UTENTE:
{query}

ISTRUZIONI:
1. Basa la tua risposta SOLO sui documenti forniti sopra
2. Se la risposta non è nei documenti, dillo chiaramente
3. Cita sempre la fonte (nome documento e pagina se disponibile)
4. Sii conciso ma completo
5. ⚠️ OBBLIGATORIO: Usa SOLO tag HTML (NON Markdown):
   - <b>grassetto</b> per concetti importanti (NON **testo**)
   - <i>corsivo</i> per termini tecnici (NON *testo*)
   - <code>code</code> per codice o comandi (NON `code`)
   - <pre>blocchi di codice</pre> per codice multilinea (NON ```code```)

RISPOSTA:"""

    RAG_NO_CONTEXT_PROMPT = """Non ho trovato informazioni rilevanti nei documenti caricati per rispondere a questa domanda.

Posso:
1. Cercare informazioni sul web (se web search è abilitato)
2. Rispondere basandomi sulla mia conoscenza generale
3. Chiederti di riformulare la domanda in modo più specifico

Come preferisci procedere?"""

    # =========================================
    # ROUTING PROMPTS
    # =========================================

    ROUTING_PROMPT = """Analizza la domanda dell'utente e decidi quale fonte usare per rispondere.

DOMANDA: {query}

FONTI DISPONIBILI:
- RAG: Documenti caricati nel database (usa per domande su materiale specifico caricato)
- WEB: Ricerca web con Tavily (usa per informazioni recenti o non presenti nei documenti)
- DIRECT: Conoscenza generale LLM (usa per domande generali che non richiedono fonti esterne)

Rispondi con UNA SOLA parola: RAG, WEB, o DIRECT

DECISIONE:"""

    # =========================================
    # WEB SEARCH PROMPTS
    # =========================================

    WEB_SEARCH_PROMPT = """Basandoti sui risultati della ricerca web, rispondi alla domanda dell'utente.

RISULTATI RICERCA WEB:
{web_results}

DOMANDA UTENTE:
{query}

ISTRUZIONI:
1. Sintetizza le informazioni più rilevanti
2. Fornisci fonti/link usando <a href="URL">testo</a>
3. Indica che le info provengono da ricerca web recente
4. Sii conciso ma informativo
5. ⚠️ OBBLIGATORIO: Usa SOLO tag HTML (NON Markdown):
   - <b>grassetto</b> per punti chiave (NON **testo**)
   - <i>corsivo</i> per enfasi (NON *testo*)
   - <code>code</code> per riferimenti tecnici (NON `code`)

RISPOSTA:"""

    # =========================================
    # VISION PROMPTS
    # =========================================

    VISION_ANALYSIS_PROMPT = """Analizza questa immagine e descrivi dettagliatamente cosa vedi.

CONTESTO UTENTE: {caption}

Fornisci un'analisi strutturata includendo:
1. Descrizione generale
2. Elementi principali
3. Testo visibile (se presente)
4. Contesto educativo (se rilevante)

⚠️ OBBLIGATORIO: Usa SOLO tag HTML per formattare (NON Markdown):
- <b>grassetto</b> per elementi importanti (NON **testo**)
- <i>corsivo</i> per descrizioni (NON *testo*)
- <code>code</code> per testo visibile nell'immagine (NON `code`)

Sii chiaro e pedagogico nella descrizione."""

    VISION_QUESTION_PROMPT = """Basandoti su questa immagine, rispondi alla domanda dell'utente.

DOMANDA: {question}

Analizza l'immagine attentamente e fornisci una risposta dettagliata e educativa.

⚠️ OBBLIGATORIO: Usa SOLO tag HTML per formattare (NON Markdown):
- <b>grassetto</b> per concetti chiave (NON **testo**)
- <i>corsivo</i> per enfasi (NON *testo*)
- <code>code</code> per riferimenti specifici (NON `code`)"""

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
/add_doc - Carica nuovo documento (PDF, DOCX, TXT)
/list_docs - Lista documenti caricati
/delete_doc - Elimina documento per ID
/stats - Statistiche sistema

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
  → Supporta: PDF, DOCX, TXT
  → Max size: 20MB
  → Il bot processerà e indicizzerà il documento

/list_docs - Mostra tutti i documenti caricati
  → Vedi ID, nome, data caricamento, numero chunks

/delete_doc <id> - Elimina documento
  → Esempio: /delete_doc doc_12345
  → Richiede conferma per sicurezza

/stats - Statistiche sistema
  → Documenti totali
  → Chunks indicizzati
  → Storage utilizzato
  → Utenti attivi

👤 COMANDI UTENTE:
/help - Mostra aiuto
/clear - Cancella cronologia
/voice_on - Attiva risposte audio
/voice_off - Disattiva risposte audio

🎓 GESTIONE DOCUMENTI:
1. Carica documenti con /add_doc
2. Verifica indicizzazione con /list_docs
3. Gli utenti possono subito fare query RAG
4. Elimina documenti obsoleti con /delete_doc"""

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

Formato ricevuto: {file_format}"""

    ERROR_PROCESSING_DOCUMENT = """❌ Errore durante il processamento del documento.

Motivo: {error}

Riprova o contatta l'amministratore se il problema persiste."""

    ERROR_GENERIC = """❌ Si è verificato un errore.

{error_message}

Riprova o usa /help per assistenza."""

    ERROR_NO_ADMIN_CONFIGURED = """⚠️ Nessun amministratore configurato!

Il bot richiede almeno un admin per funzionare.
Configura ADMIN_USER_IDS nel file .env o Replit Secrets."""

    ERROR_API_KEY_MISSING = """❌ API key mancante: {key_name}

Configura la key in:
• Locale: file .env
• Replit: Secrets

Vedi .env.example per riferimento."""

    # =========================================
    # CONFIRMATION MESSAGES
    # =========================================

    CONFIRM_DELETE_DOCUMENT = """⚠️ CONFERMA ELIMINAZIONE

Stai per eliminare:
📄 Nome: {filename}
🆔 ID: {doc_id}
📊 Chunks: {num_chunks}

Questa azione è IRREVERSIBILE!

Rispondi con:
✅ /confirm_delete - Per confermare
❌ /cancel - Per annullare"""

    CONFIRM_CLEAR_MEMORY = """⚠️ CONFERMA CANCELLAZIONE MEMORIA

Stai per cancellare tutta la cronologia della conversazione.

Questa azione è IRREVERSIBILE!

Rispondi con:
✅ /confirm_clear - Per confermare
❌ /cancel - Per annullare"""

    MEMORY_CLEARED = """✅ Memoria conversazione cancellata!

Possiamo ricominciare da zero. Come posso aiutarti?"""

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
# HELPER FUNCTIONS
# =========================================

def format_sources(sources: list) -> str:
    """
    Formatta lista di fonti per citazioni.

    Args:
        sources: Lista di dict con 'source' e 'page'

    Returns:
        Stringa formattata con citazioni
    """
    if not sources:
        return ""

    citations = "\n\n📚 **Fonti:**\n"
    for i, source in enumerate(sources, 1):
        filename = source.get('source', 'Unknown')
        page = source.get('page', 'N/A')
        citations += f"{i}. {filename} (pag. {page})\n"

    return citations


def truncate_text(text: str, max_length: int = 4000) -> str:
    """
    Tronca testo se supera max_length.

    Utile per rispettare limiti Telegram (4096 chars) e TTS (4096 chars).

    Args:
        text: Testo da troncare
        max_length: Lunghezza massima

    Returns:
        Testo troncato con ellipsis se necessario
    """
    if len(text) <= max_length:
        return text

    return text[:max_length-3] + "..."


def format_error_for_user(error: Exception) -> str:
    """
    Formatta errore tecnico in messaggio user-friendly.

    Args:
        error: Eccezione Python

    Returns:
        Messaggio di errore comprensibile
    """
    error_str = str(error).lower()

    # Map errori comuni a messaggi user-friendly
    if "rate limit" in error_str:
        return "Troppe richieste. Attendi un momento e riprova."
    elif "timeout" in error_str:
        return "Richiesta scaduta. Riprova con una query più semplice."
    elif "api key" in error_str:
        return "Errore di autenticazione API. Contatta l'amministratore."
    elif "quota" in error_str:
        return "Quota API esaurita. Contatta l'amministratore."
    else:
        return f"Errore: {str(error)[:100]}"


# =========================================
# EXPORTS
# =========================================
prompts = Prompts()


if __name__ == "__main__":
    # Fix UTF-8 encoding per Windows
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    # Test prompts
    print("Testing prompts module...")
    print("\n=== WELCOME MESSAGE ===")
    print(prompts.WELCOME_USER)
    print("\n=== RAG QUERY EXAMPLE ===")
    print(prompts.RAG_QUERY_PROMPT.format(
        context="Example document content...",
        query="What is machine learning?"
    ))
    print("\n✅ All prompts loaded successfully!")
