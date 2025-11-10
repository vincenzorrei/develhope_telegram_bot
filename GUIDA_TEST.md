# 🧪 GUIDA AL TESTING DEL BOT

## ✅ Test Base Completato

Hai già eseguito con successo il **test rapido** che verifica:
- ✅ Tutti i moduli Python si importano correttamente (16/16)
- ✅ Tutte le classi sono sintatticamente corrette
- ✅ Le dipendenze sono installate

**Risultato: TUTTO OK!** 🎉

---

## 📋 PROSSIMI STEP DI TEST

### Opzione A: Test Completo con Chiavi Reali (Consigliato)
### Opzione B: Test Solo ChromaDB (Senza OpenAI/Telegram)
### Opzione C: Demo Offline Componenti

---

## 🔑 OPZIONE A: Test Completo con Chiavi Reali

### Step 1: Ottieni le API Keys

#### 1.1 Telegram Bot Token

**Tempo: 2 minuti**

1. Apri **Telegram** sul telefono/desktop
2. Cerca **@BotFather** (è ufficiale, ha check blu)
3. Invia il comando: `/newbot`
4. Segui le istruzioni:
   - Nome del bot (es: "Il Mio EduBot")
   - Username del bot (deve finire con "bot", es: "mio_edubot")
5. **BotFather ti darà un TOKEN**:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz-1234567
   ```
6. **COPIA QUESTO TOKEN** (lo usi dopo)

#### 1.2 Telegram User ID (per admin)

**Tempo: 30 secondi**

1. Su Telegram, cerca **@userinfobot**
2. Invia `/start`
3. Ti risponderà con il tuo **User ID** (numero, es: `123456789`)
4. **COPIA QUESTO NUMERO**

#### 1.3 OpenAI API Key

**Tempo: 5 minuti + costo $5 minimo**

1. Vai su [platform.openai.com](https://platform.openai.com)
2. **Registrati** (serve email + numero telefono)
3. Vai su **Settings → Billing** → **Add Payment Method**
   - ⚠️ **IMPORTANTE:** Devi aggiungere **minimo $5** di credito
4. Vai su **API Keys** → **Create new secret key**
5. **COPIA LA KEY** (inizia con `sk-...`)
   - ⚠️ La vedrai **solo una volta**! Salvala subito

**Costi stimati:**
- Embeddings: ~$0.02 per 1M tokens
- Chat: ~$0.15-0.60 per 1M tokens
- **Per test (10-20 query):** ~$0.10-0.50

#### 1.4 Tavily API Key (Web Search - OPZIONALE)

**Tempo: 2 minuti | FREE 1000 ricerche/mese**

1. Vai su [tavily.com](https://tavily.com)
2. Registrati (email)
3. Dashboard → **Copia API Key** (inizia con `tvly-...`)

**Puoi anche testare senza Tavily** (il bot funzionerà comunque, solo senza web search)

---

### Step 2: Configura il file .env

Apri il file `.env` nella root del progetto e modifica:

```bash
# ==========================================
# API KEYS - SOSTITUISCI CON LE TUE REALI
# ==========================================

# Telegram (da @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz-1234567

# OpenAI (da platform.openai.com)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxx

# Tavily Web Search (da tavily.com) - OPZIONALE
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxxxx

# Admin User IDs (da @userinfobot) - Separati da virgola se più di uno
ADMIN_USER_IDS=123456789

# ==========================================
# CONFIGURAZIONI OPZIONALI
# ==========================================

# Nome del bot (opzionale)
BOT_NAME=EduBot RAG

# Environment (opzionale)
ENVIRONMENT=local
```

**Salva il file!**

---

### Step 3: Avvia il Bot

Nel terminale, dalla root del progetto:

```bash
python main.py
```

**Output atteso:**

```
============================================================
SYSTEM STARTUP - Bot Telegram Educativo con RAG
============================================================
Start Time: 2025-11-04 12:45:00
Python: 3.11.x
Platform: Windows
============================================================

[CONFIG] VALIDAZIONE CONFIGURAZIONE
[OK] TELEGRAM_BOT_TOKEN configurato
[OK] OPENAI_API_KEY configurato
[OK] TAVILY_API_KEY configurato
[OK] Admin configurati: 1
[OK] LLM Model: gpt-4o-mini
[OK] Embedding Model: text-embedding-3-small
[OK] RAG Top-K: 3

============================================================
INITIALIZING COMPONENTS
============================================================

[1/5] Initializing Vector Store...
[VECTORDB] Inizializzazione ChromaDB...
[OK] Collection 'documents' ready (0 documenti)
[OK] Vector Store ready

[2/5] Initializing Document Processor...
[INIT] DocumentProcessor
       Chunk size: 800
       Chunk overlap: 100
[OK] Text splitter configured
[OK] Document Processor ready

[3/5] Initializing LangChain Engine...
[ENGINE] Inizializzazione LangChain Engine...
[OK] LLM model: gpt-4o-mini
[OK] Embeddings: text-embedding-3-small
[OK] Tools: 2 (RAG Search, Web Search)
[OK] Agent: ReAct pattern configured
[OK] LangChain Engine ready

[4/5] Initializing Message Processor...
[OK] Message Processor ready

[5/5] Initializing Telegram Bot...
[OK] Telegram Bot ready

============================================================
ALL COMPONENTS INITIALIZED SUCCESSFULLY
============================================================

[HANDLERS] Registering handlers...
[OK] All handlers registered
      Admin: 4 commands
      User: 5 commands
      Message: 3 types

============================================================
BOT STARTING - POLLING MODE
============================================================
Bot is now running! Press CTRL+C to stop.
============================================================
```

**Se vedi questo output: IL BOT È IN ESECUZIONE!** ✅

---

### Step 4: Test Funzionalità su Telegram

#### 4.1 Test Comandi Base

1. **Apri Telegram** sul telefono/desktop
2. **Cerca il tuo bot** (l'username che hai scelto)
3. **Premi START** o invia `/start`

**Output atteso:**
```
Ciao! Sono EduBot RAG, il tuo assistente educativo intelligente.

Posso aiutarti con:
- Rispondere a domande sui documenti caricati (RAG)
- Cercare informazioni aggiornate sul web
- Analizzare immagini
- Generare risposte vocali

Comandi disponibili:
/help - Mostra tutti i comandi
/clear - Cancella cronologia conversazione
/voice_on - Attiva risposte vocali
/voice_off - Disattiva risposte vocali

[ADMIN COMMANDS]
/add_doc - Carica documento
/list_docs - Lista documenti
/delete_doc <id> - Elimina documento
/stats - Statistiche sistema
```

4. **Invia `/help`** → Vedi lista completa comandi

#### 4.2 Test Conversazione Base

5. **Invia una domanda semplice:**
```
Ciao, puoi presentarti?
```

**Il bot dovrebbe rispondere** (potrebbe impiegare 3-5 secondi)

6. **Prova una domanda che richiede web search:**
```
Chi ha vinto il mondiale di calcio 2022?
```

**Il bot dovrebbe:**
- Usare il tool "ricerca_web" (Tavily)
- Rispondere con informazioni aggiornate

Nel terminale vedrai i log:
```
[MSG] User 123456789: 'Chi ha vinto il mondiale di calcio 2022?...'
[AGENT] Calling tool: ricerca_web
[WEB] Query: "mondiale calcio 2022 vincitore"
[AGENT] Response generated
```

#### 4.3 Test Caricamento Documento (ADMIN)

7. **Invia il comando:**
```
/add_doc
```

**Bot risponde:**
```
Invia il documento (PDF, DOCX, o TXT) che vuoi caricare.

Formati supportati:
- PDF (.pdf)
- Word (.docx)
- Testo (.txt)

Max dimensione: 20MB
```

8. **Invia un file PDF di test** (es: un documento di 2-3 pagine)
   - Usa il pulsante 📎 per allegare file
   - Oppure trascina il file nella chat

**Bot processa il documento:**
```
Documento ricevuto, elaborazione in corso...

[SUCCESS] Documento aggiunto con successo!

File: esempio.pdf
Chunks creati: 5
Doc ID: doc_exemplo_1730730000

Totale documenti nel sistema: 1
```

Nel terminale vedrai:
```
[DOC] Received: esempio.pdf (45.3 KB)
[PDF] Loading: C:\Users\...\tmp_exemplo.pdf
      PDF has 3 pages
[OK] Extracted 2450 characters
[CHUNK] Splitting text (2450 chars)...
[OK] Created 5 chunks
      Avg chunk length: 490 chars
[VECTORDB] Adding 5 chunks...
[OK] Added 5 chunks to collection
[COPY] Saved to: ./data/documents/doc_exemplo_1730730000_exemplo.pdf
[SUCCESS] Processed document
```

9. **Verifica documento caricato:**
```
/list_docs
```

**Risposta:**
```
Documenti caricati (1):

1. esempio.pdf
   ID: doc_exemplo_1730730000
   Chunks: 5
   Data: 2025-11-04
```

#### 4.4 Test Query RAG

10. **Fai una domanda sul documento caricato:**
```
Dimmi di cosa parla il documento che hai caricato
```

**Il bot dovrebbe:**
- Usare il tool "ricerca_documenti"
- Recuperare i chunk rilevanti dal ChromaDB
- Rispondere basandosi sul contenuto

**Risposta attesa** (esempio):
```
In base ai documenti caricati, posso dirti che...

[FONTI]
- esempio.pdf (chunks: 1, 3)
```

Nel terminale:
```
[AGENT] Calling tool: ricerca_documenti
[RAG] Query: "contenuto documento"
[VECTORDB] Similarity search (top_k=3)
[RAG] Found 3 relevant chunks
[AGENT] Response generated with citations
```

#### 4.5 Test Immagini (Vision)

11. **Invia un'immagine** (screenshot, foto, diagramma)
    - Con o senza caption

**Bot analizza con GPT-4o Vision:**
```
[Analisi immagine]

Vedo un'immagine che mostra...
[descrizione dettagliata]
```

Nel terminale:
```
[IMAGE] User 123456789 sent image
[VISION] Processing with GPT-4o...
[VISION] Analysis completed
```

#### 4.6 Test Risposte Vocali (TTS)

12. **Attiva modalità voce:**
```
/voice_on
```

**Bot:**
```
Modalità voce attivata!
Le prossime risposte includeranno anche audio.
```

13. **Invia una domanda:**
```
Spiegami cos'è il machine learning
```

**Bot risponde con:**
- Messaggio di testo
- **+ File audio MP3** (voce sintetizzata OpenAI TTS)

⚠️ **ATTENZIONE:** TTS costa ~$15 per 1M caratteri. Usa con moderazione!

14. **Disattiva voce:**
```
/voice_off
```

#### 4.7 Test Memoria Conversazionale

15. **Invia una serie di messaggi correlati:**

```
Tu: Qual è la capitale della Francia?
Bot: La capitale della Francia è Parigi.

Tu: E quanti abitanti ha?
Bot: Parigi ha circa 2.1 milioni di abitanti...
     [dovrebbe ricordare che stai parlando di Parigi]

Tu: Parlami della torre più famosa
Bot: La Torre Eiffel è il monumento più iconico di Parigi...
     [dovrebbe ricordare il contesto: Francia → Parigi → Torre]
```

16. **Cancella memoria:**
```
/clear
```

**Bot:**
```
Cronologia conversazione cancellata.
Possiamo ricominciare da capo!
```

17. **Verifica che ha dimenticato:**
```
Tu: Di cosa stavamo parlando?
Bot: Non ho memoria di conversazioni precedenti...
```

#### 4.8 Test Statistiche (ADMIN)

18. **Verifica stats sistema:**
```
/stats
```

**Risposta:**
```
=== STATISTICHE SISTEMA ===

[DOCUMENTI]
Totale documenti: 1
Totale chunks: 5
Collection: documents

[STORAGE]
Vector DB: 0.05 MB
Documenti originali: 0.05 MB
Totale: 0.10 MB
Limite Railway (Hobby): 512 MB RAM / 512 MB Disk

[UTENTI]
Utenti attivi: 1
Admin: 1

[CONFIGURAZIONE]
LLM: gpt-4o-mini
Embeddings: text-embedding-3-small
RAG Top-K: 3
```

#### 4.9 Test Eliminazione Documento

19. **Elimina documento:**
```
/delete_doc doc_exemplo_1730730000
```

**Bot:**
```
Documento eliminato con successo!
Doc ID: doc_exemplo_1730730000
Nome: exemplo.pdf
```

20. **Verifica lista vuota:**
```
/list_docs
```

**Risposta:**
```
Nessun documento trovato nel sistema.

Gli admin possono caricare documenti con /add_doc
```

---

## ✅ CHECKLIST TEST COMPLETO

- [ ] Bot si avvia senza errori
- [ ] `/start` risponde correttamente
- [ ] `/help` mostra comandi
- [ ] Conversazione base funziona
- [ ] Web search con Tavily funziona
- [ ] Caricamento documento PDF funziona
- [ ] `/list_docs` mostra documenti
- [ ] Query RAG con citazioni funziona
- [ ] Analisi immagini con Vision funziona
- [ ] TTS genera audio (opzionale)
- [ ] Memoria conversazionale mantiene contesto
- [ ] `/clear` cancella memoria
- [ ] `/stats` mostra statistiche
- [ ] `/delete_doc` elimina documenti
- [ ] Comandi admin bloccati per non-admin (testa con altro utente)

**Se tutto ✅ → IL BOT FUNZIONA PERFETTAMENTE!** 🎉

---

## 🔧 OPZIONE B: Test Solo ChromaDB (Senza API Keys)

Se non vuoi usare API keys reali per ora, puoi testare solo il sistema di vector database:

```bash
python -c "
from src.rag.vector_store import VectorStoreManager
from src.rag.document_processor import DocumentProcessor

# Inizializza vector store
vs = VectorStoreManager()
print('[OK] VectorStore inizializzato')

# Inizializza processor
proc = DocumentProcessor()
print('[OK] DocumentProcessor inizializzato')

# Test chunking
text = 'Questo è un test. ' * 100
chunks = proc.chunk_text(text)
print(f'[OK] Creati {len(chunks)} chunks')

# Test add documento
metadatas = [{'source': 'test.txt', 'chunk_index': i} for i in range(len(chunks))]
vs.add_document(chunks, metadatas, 'test_doc')
print('[OK] Documento aggiunto')

# Test search
results = vs.similarity_search('test', k=3)
print(f'[OK] Trovati {len(results)} risultati')

# Stats
stats = vs.get_stats()
print(f'[OK] Stats: {stats}')
"
```

---

## 📊 OPZIONE C: Demo Offline Componenti

Test individuali senza API keys:

### Test Document Processor
```bash
python src/rag/document_processor.py
```

### Test Vector Store
```bash
python src/rag/vector_store.py
```

### Test Logger
```bash
python src/utils/logger.py
```

### Test Helpers
```bash
python src/utils/helpers.py
```

---

## ❌ TROUBLESHOOTING

### Errore: "Unauthorized" (401)
**Causa:** Token Telegram non valido
**Fix:** Verifica che il token in `.env` sia corretto (da @BotFather)

### Errore: "Invalid API key" (401) OpenAI
**Causa:** Key OpenAI non valida o senza credito
**Fix:**
1. Verifica key in `.env`
2. Controlla credito su platform.openai.com

### Bot non risponde su Telegram
**Causa:** Bot non in esecuzione o token errato
**Fix:**
1. Verifica che `python main.py` sia in esecuzione
2. Controlla log nel terminale per errori

### "No documents found" in RAG query
**Causa:** Nessun documento caricato
**Fix:** Usa `/add_doc` per caricare almeno un documento

### ChromaDB errors
**Causa:** Database corrotto
**Fix:** Elimina `./data/vectordb/` e riavvia bot

---

## 💰 COSTI STIMATI

**Test completo (20-30 query):**
- Embeddings (1 doc, 5 chunks): ~$0.001
- Chat (20 query): ~$0.05-0.20
- Vision (3 immagini): ~$0.01-0.05
- TTS (se usato, 2 risposte): ~$0.02-0.10

**Totale test:** ~$0.10-0.40 USD

**Uso mensile educativo (100 query):**
- Chat: ~$1-2
- Vision: ~$0.10-0.50
- Embeddings (10 doc): ~$0.05
- **Senza TTS:** $1-3/mese
- **Con TTS:** +$10-20/mese (COSTOSO!)

---

## 🎓 DOPO IL TEST

Una volta verificato che tutto funziona:

### Personalizzazione Livello 1
Modifica `config.py`:
```python
LLM_TEMPERATURE = 0.8  # Più creativo
RAG_TOP_K = 5          # Più documenti
CHUNK_SIZE = 1000      # Chunks più grandi
```

### Personalizzazione Livello 2
Modifica `prompts.py`:
```python
SYSTEM_PROMPT = """
Sei un tutor specializzato in [TUA MATERIA].
Spiega sempre con esempi pratici...
"""
```

### Personalizzazione Livello 3
Aggiungi tools in `bot_engine.py` (vedi esercizi nel file)

---

## 📞 SUPPORTO

Se hai problemi:
1. Controlla log nel terminale
2. Verifica `.env` configurato correttamente
3. Consulta README.md sezione Troubleshooting
4. Verifica credito OpenAI

---

**Buon test! 🚀**
