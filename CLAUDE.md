# SYSTEM PROMPT - Telegram AI Bot Educativo con RAG e LangChain

## 🎯 OBIETTIVO

Creare un bot Telegram educativo con RAG, LangChain agents e multimodalità per studenti al **primo progetto Python**.

**Target:**
- Studenti neofiti (zero esperienza Python/AI)
- Focus: imparare LangChain/RAG, non DevOps
- Ogni studente crea e deploya il proprio bot

**Caso d'uso:**
Bot Telegram che risponde usando:
- Documenti caricati (RAG con ChromaDB)
- Web search (Tavily)
- Immagini (GPT-4o Vision) e audio (OpenAI TTS)
- Gestione documenti via comandi Telegram admin

---

## 📚 DOCUMENTAZIONE DI RIFERIMENTO

Il repository contiene `research.md` con analisi tecnica completa per costruire il bot su Railway Hobby Plan, includendo:
- Architettura ottimale
- Workaround tecnici critici
- Best practices LangChain 0.3.x
- Strategie deployment
- Troubleshooting comune

**Consulta sempre `research.md` per decisioni architetturali e implementative.**

---

## 📋 STACK TECNOLOGICO OBBLIGATORIO

### Versioni Critiche
```
python-telegram-bot==22.5        # Asyncio-based, polling only
langchain==0.3.22                # LangChain 0.3.x family
langchain-openai==0.3.11
langchain-community==0.3.20
openai==1.68.0                   # v1.x API
chromadb>=0.4.22,<0.5.0          # CRITICO: <0.5.0
pypdf==4.0.0                     # NON PyPDF2 (deprecato)
python-docx==1.1.0
tavily-python==0.5.0
pysqlite3-binary==0.5.2          # Workaround SQLite Railway
```

### Python Version
**Python 3.11** (NON 3.12+ per incompatibilità ChromaDB)

### Deployment
- **Primario**: Railway Hobby Plan ($5/mese) con polling
- **Secondario**: Locale
- **NO webhook**: Solo polling (requisito Railway Hobby Plan - limitazioni RAM 0.5GB)

---

## 🏗️ STRUTTURA CARTELLE
```
telegram-ai-bot/
├── 📄 README.md                    # Guida studenti (italiano)
├── 📄 README_SETUP_RAILWAY.md      # Setup Railway step-by-step
├── 📄 README_SETUP_LOCAL.md        # Setup locale
├── 📄 research.md                  # ⭐ ANALISI TECNICA COMPLETA
│
├── 🚀 main.py                      # ⭐ ENTRY POINT
├── ⚙️ config.py                    # ⭐ STUDENTI MODIFICANO
├── 💬 prompts.py                   # ⭐ STUDENTI MODIFICANO
├── 🧠 langchain_core.py            # ⭐ CUORE DIDATTICO
│
├── 📦 requirements.txt
├── 📦 .env.example
├── 📦 .gitignore
│
├── 📂 src/
│   ├── 📂 telegram/
│   │   ├── bot_setup.py           # Inizializzazione bot
│   │   ├── handlers.py            # Handler comandi/messaggi (async)
│   │   ├── auth.py                # Middleware autenticazione
│   │   └── message_processor.py   # Processing testo/immagini/audio
│   │
│   ├── 📂 rag/
│   │   ├── vector_store.py        # ChromaDB wrapper (PersistentClient)
│   │   ├── document_processor.py  # Caricamento/chunking (pypdf)
│   │   └── retriever.py           # Query e retrieval
│   │
│   ├── 📂 llm/
│   │   ├── audio.py               # OpenAI TTS
│   │   └── image_processor.py     # GPT-4o Vision
│   │
│   └── 📂 utils/
│       ├── conversation_manager.py # Memoria per user_id
│       ├── logger.py              # Logging configurabile
│       └── helpers.py             # Utility functions
│
├── 📂 data/                       # ⚠️ AUTO-GENERATO (gitignore)
│   ├── vectordb/                  # ChromaDB SQLite
│   ├── documents/                 # File originali
│   └── conversations/             # Backup chat (opzionale)
│
└── 📂 docs/                       # Documentazione extra
    ├── ARCHITECTURE.md
    ├── LANGCHAIN_GUIDE.md
    ├── EXERCISES.md
    └── TROUBLESHOOTING.md
```

---

## 🔧 SPECIFICHE IMPLEMENTAZIONE

### 📄 main.py - Entry Point

**Responsabilità:**
1. Setup workaround SQLite per Railway (se necessario)
2. Creazione cartelle necessarie
3. Inizializzazione: ChromaDB → LangChain → Telegram Bot
4. Avvio polling Telegram
5. Gestione graceful shutdown (CTRL+C)

**Flow obbligatorio:**
- Workaround SQLite PRIMA di qualsiasi import
- Verifica API keys (exit se mancanti)
- Inizializzazione sequenziale componenti
- Error handling robusto
- Logging con emoji per UX studenti

---

### ⚙️ config.py - Configurazione

**MODIFICABILE dagli studenti.**

**Contenuto minimo:**
- API Keys (da env): `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `TAVILY_API_KEY`
- Admin user IDs: `ADMIN_USER_IDS = [123456789]`
- Impostazioni bot: model, temperature, voice, feature flags
- Impostazioni RAG: top_k, chunk_size, overlap, embedding model
- Impostazioni LangChain: temperature, max iterations, verbose
- Paths: data directories

**CRITICO:** Workaround SQLite DEVE essere PRIMA di import chromadb:
```python
import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass
```

---

### 💬 prompts.py - Prompts Centralizzati

**MODIFICABILE dagli studenti per sperimentare.**

**Struttura classe `Prompts`:**
- `SYSTEM_PROMPT`: Comportamento generale bot
- `RAG_QUERY_PROMPT`: Template query con documenti
- `WELCOME_USER`: Messaggio benvenuto utenti
- `WELCOME_ADMIN`: Messaggio benvenuto admin con comandi
- `NO_DOCUMENTS_FOUND`: Errore documenti vuoti
- `DOCUMENT_ADDED`: Conferma caricamento
- `UNAUTHORIZED`: Accesso negato non-admin

---

### 🧠 langchain_core.py - CUORE DIDATTICO

**File PIÙ IMPORTANTE - PESANTEMENTE commentato per studenti.**

**ATTENZIONI CRITICHE:**
- ❌ `initialize_agent` è DEPRECATO in LangChain 0.3.x
- ✅ Usare `create_react_agent` + `AgentExecutor`
- ✅ Prompt da hub: `hub.pull("hwchase17/react-chat")`

**Classe `LangChainEngine`:**

**Componenti da inizializzare:**
1. LLM: `ChatOpenAI` con model e temperature configurabili
2. Embeddings: `OpenAIEmbeddings` per RAG
3. Vector Store: ChromaDB wrapper
4. Memory: dizionario per user_id → `ConversationBufferMemory`
5. Tools: RAG + Web Search
6. Agent: ReAct pattern con `create_react_agent`

**Metodi principali:**

- `_setup_tools()`: Crea lista Tool objects
  - Tool RAG: `ricerca_documenti` con description chiara
  - Tool Web: `TavilySearchResults` per ricerche online
  
- `_setup_agent()`: Crea AgentExecutor con ReAct pattern
  - Usa `hub.pull("hwchase17/react-chat")`
  - `create_react_agent(llm, tools, prompt)`
  - `AgentExecutor` con verbose, max_iterations, error handling

- `_get_or_create_memory(user_id)`: Memoria separata per utente

- `_search_documents(query)`: Pipeline RAG completa
  1. **RETRIEVAL**: Similarity search (top_k chunks)
  2. **AUGMENTATION**: Costruisci prompt con contesto
  3. **GENERATION**: LLM genera risposta
  4. **CITATION**: Aggiungi fonti

- `process_message(user_message, user_id)`: Entry point principale
  - Recupera memoria utente
  - Agent decide automaticamente tool da usare
  - Aggiorna memoria conversazione
  - Return risposta

- `process_image(image_bytes, caption, user_id)`: GPT-4o Vision
  - Converti immagine in base64
  - Chiamata OpenAI Vision API
  - Return descrizione/analisi

- `generate_audio(text)`: Text-to-Speech OpenAI
  - Limita testo a 4096 caratteri
  - Return bytes MP3

- `clear_memory(user_id)`: Pulisci cronologia utente

**Esercizi progressivi inline:**
- Livello 1: Modifica temperature, top_k
- Livello 2: Personalizza prompts
- Livello 3: Aggiungi nuovo tool
- Livello 4: Migliora routing, feedback loop

---

### 📂 src/telegram/

#### handlers.py

**TUTTI gli handler DEVONO essere `async def`.**

**Handler Admin (decoratore `@admin_only`):**
- `add_doc_handler`: Inizia flow caricamento
- `document_handler`: Riceve file, processa, aggiungi ChromaDB
- `list_docs_handler`: Mostra documenti caricati
- `delete_doc_handler`: Elimina documento per ID
- `stats_handler`: Statistiche sistema

**Handler User (decoratore `@user_or_admin`):**
- `start_handler`: Benvenuto (messaggio diverso admin/user)
- `help_handler`: Lista comandi disponibili
- `clear_handler`: Pulisci cronologia conversazione
- `voice_on_handler` / `voice_off_handler`: Toggle audio

**Handler Messaggi:**
- `message_handler`: Processa testo normale
  - LangChain processing
  - Risposta testo + audio se voice_mode attivo
- `image_handler`: Processa immagini
  - Download highest resolution
  - GPT-4o Vision processing

**Funzione `setup_handlers`:**
- Registra tutti handler nell'Application
- Store references (langchain_engine, vector_store, document_processor) in bot_data
- Add command handlers + message handlers

#### auth.py

Decoratori autenticazione:
- `@admin_only`: Verifica user_id in ADMIN_USER_IDS
- `@user_or_admin`: Tutti possono (opzionale: whitelist)

#### bot_setup.py

Funzione `create_bot(token)`:
- Return `Application.builder().token(token).build()`

---

### 📂 src/rag/

#### vector_store.py

**Classe `VectorStoreManager`:**

**CRITICO:** Usare `chromadb.PersistentClient` (NON `Client()` ephemeral)

**Metodi:**
- `__init__`: Inizializza PersistentClient con path, get_or_create_collection
- `add_document(chunks, metadatas, doc_id)`: Aggiungi chunks con IDs univoci
- `delete_document(doc_id)`: Elimina tutti chunks documento
- `list_all_documents()`: Lista documenti con metadata aggregati
- `similarity_search(query, k)`: Query vector store, return results
- `get_stats()`: Statistiche (total_chunks, total_documents)

#### document_processor.py

**Classe `DocumentProcessor`:**

**ATTENZIONE:** Usare `pypdf` (NON PyPDF2 deprecato)

**Metodi:**
- `__init__`: Setup `RecursiveCharacterTextSplitter` con chunk_size, overlap
- `load_pdf(filepath)`: Usa `pypdf.PdfReader`
- `load_docx(filepath)`: Usa `python-docx.Document`
- `load_txt(filepath)`: Leggi UTF-8
- `load_document(filepath, file_type)`: Router per tipo
- `chunk_text(text)`: Split con text_splitter
- `process_and_add(filepath, filename, vector_store)`: Pipeline completo
  1. Carica documento
  2. Chunking
  3. Genera metadata (doc_id, timestamp, chunk_index)
  4. Aggiungi a vector store
  5. Return num_chunks

---

### 📂 src/llm/

#### audio.py
- Wrapper OpenAI TTS
- Text-to-Speech con voice configurabile

#### image_processor.py
- Wrapper GPT-4o Vision
- Analisi immagini con OpenAI Vision API

---

### 📂 src/utils/

#### logger.py
- Setup logging configurabile
- Log file + console con formattazione

#### conversation_manager.py
- Gestione memoria conversazionale per user_id
- Salvataggio/caricamento cronologie (opzionale)

#### helpers.py
- Utility functions generiche
- Format helpers, validators

---

## 🎨 STILE CODICE OBBLIGATORIO

### Commenti
- **Docstrings Google Style** per TUTTE le funzioni/classi
- **Commenti inline** per logica non ovvia
- **Sezioni con banner** per separare logicamente
- **Emoji nei print/log** per UX studenti (✅ ❌ 🤖 📊 🧠 etc.)

### Docstring Template:
```python
def method_name(self, param: type) -> return_type:
    """
    Breve descrizione metodo.
    
    Descrizione dettagliata con steps se necessario:
    1. Step 1
    2. Step 2
    
    Args:
        param: Descrizione parametro
        
    Returns:
        Descrizione return value
        
    Raises:
        ExceptionType: Quando solleva eccezione
        
    Example:
        >>> result = obj.method_name(value)
        >>> print(result)
    """
```

### Error Handling
- Try-except su TUTTE le operazioni critiche
- Log errori con traceback completo
- Messaggi user-friendly su Telegram
- Bot NON deve MAI crashare

**Pattern obbligatorio:**
```python
try:
    # operazione critica
except Exception as e:
    logger.error(f"Errore: {e}")
    import traceback
    traceback.print_exc()
    # messaggio utente + fallback
```

---

## 📖 DOCUMENTAZIONE README

### README.md (italiano, studenti)

**Sezioni obbligatorie:**
1. **Introduzione**: Cosa fa, perché utile, features principali
2. **Quick Start Railway**: Setup 10-15 minuti con link a setup dettagliato
3. **Quick Start Locale**: Setup dettagliato con prerequisiti
4. **Struttura Progetto**: Spiegazione cartelle e file chiave
5. **Comandi Disponibili**: Tabella Admin vs User commands
6. **Personalizzazione**: Come modificare config.py e prompts.py
7. **FAQ**: Problemi comuni + soluzioni
8. **Esercizi**: Link a docs/EXERCISES.md con esercizi progressivi
9. **Risorse**: Link documentazione LangChain, OpenAI, ChromaDB
10. **Licenza & Contributi**

### README_SETUP_RAILWAY.md

Step-by-step illustrato con:
- Screenshot testuali ASCII art
- Numerazione chiara
- Verifiche intermediate ("Checkpoint")
- Troubleshooting inline

### README_SETUP_LOCAL.md

Include:
- Prerequisiti (Python 3.11, pip, git)
- Virtual environment setup
- Installazione dipendenze
- File .env configuration con esempio
- Esecuzione bot
- Troubleshooting SQLite e dipendenze

---

## ⚠️ PROBLEMI CRITICI DA EVITARE

### 1. ChromaDB su Railway
**PROBLEMA:** Possibili incompatibilità SQLite version
**SOLUZIONE:** Workaround pysqlite3 PRIMA di ogni import chromadb (se necessario)

### 2. LangChain Agent Deprecation
**PROBLEMA:** `initialize_agent` deprecato in 0.3.x  
**SOLUZIONE:** `create_react_agent` + `AgentExecutor`

### 3. PyPDF2 Deprecation
**PROBLEMA:** PyPDF2 è deprecato  
**SOLUZIONE:** Usare pypdf (successore ufficiale)

### 4. ChromaDB Breaking Changes
**PROBLEMA:** ChromaDB 0.5.x+ ha breaking changes  
**SOLUZIONE:** Pin `chromadb>=0.4.22,<0.5.0`

### 5. Asyncio Pattern
**PROBLEMA:** python-telegram-bot v20+ è tutto asyncio  
**SOLUZIONE:** TUTTI handler `async def` con `await`

### 6. ChromaDB Persistence
**PROBLEMA:** `Client()` è ephemeral (perde dati)  
**SOLUZIONE:** `PersistentClient(path=...)` con path configurato

### 7. Telegram File Size
**PROBLEMA:** Telegram ha limiti dimensioni file  
**SOLUZIONE:** Check `document.file_size` prima processing (max 20MB)

---

## 🎯 CHECKLIST PRE-COMMIT

### Codice
- [ ] Tutti file creati secondo struttura
- [ ] main.py eseguibile senza errori
- [ ] langchain_core.py commentato++ con esempi
- [ ] Tutti handler async con await
- [ ] Auth decoratori applicati correttamente
- [ ] ChromaDB PersistentClient usato (NON Client)
- [ ] pypdf usato (NON PyPDF2)
- [ ] create_react_agent usato (NON initialize_agent)
- [ ] Error handling robusto ovunque
- [ ] Logging con emoji per UX
- [ ] SQLite workaround in config.py

### Testing
- [ ] Bot avvia senza errori su Railway
- [ ] Bot avvia senza errori in locale
- [ ] /start risponde correttamente (admin vs user)
- [ ] /add_doc carica documento PDF/DOCX/TXT
- [ ] /list_docs mostra documenti con metadata
- [ ] /delete_doc elimina documento
- [ ] Query RAG funzionanti con citazioni fonti
- [ ] Web search funziona (con Tavily key)
- [ ] Immagini processate con GPT-4o Vision
- [ ] Audio TTS generato con OpenAI
- [ ] Voice toggle funziona (/voice_on, /voice_off)
- [ ] Memory conversazionale separata per user_id
- [ ] Admin commands bloccati per non-admin
- [ ] /clear pulisce memoria utente

### Documentazione
- [ ] README.md completo in italiano
- [ ] README_SETUP_RAILWAY.md step-by-step
- [ ] README_SETUP_LOCAL.md dettagliato
- [ ] research.md incluso nella repo
- [ ] Commenti inline abbondanti
- [ ] Docstrings su tutte funzioni/classi
- [ ] .env.example con variabili spiegate
- [ ] .gitignore corretto (data/, .env, __pycache__)

### Deployment
- [ ] requirements.txt completo con versioni pinned
- [ ] Python 3.11 specificato
- [ ] Testato su Railway Hobby Plan
- [ ] Testato in locale (Mac/Linux/Windows)
- [ ] data/ in .gitignore
- [ ] Secrets mai committate
- [ ] Polling funziona (NO webhook needed)

---

## 💡 PRIORITÀ SVILUPPO

### Fase 1: Core (Obbligatorio)
1. `main.py` con SQLite workaround e setup completo
2. `config.py` con tutte configurazioni
3. `prompts.py` con tutti prompts
4. `langchain_core.py` completo e commentato++
5. `src/telegram/bot_setup.py` + `handlers.py` + `auth.py`
6. `src/rag/vector_store.py` (PersistentClient)
7. `src/rag/document_processor.py` (pypdf)
8. README.md base funzionale

### Fase 2: Multimodalità (Importante)
9. `src/llm/audio.py` (OpenAI TTS)
10. `src/llm/image_processor.py` (GPT-4o Vision)
11. Handler immagini in handlers.py
12. Voice toggle logic in handlers.py

### Fase 3: Polish (Nice to have)
13. `src/utils/logger.py` con formattazione
14. `src/utils/conversation_manager.py` (opzionale)
15. `src/utils/helpers.py` utilities
16. README_SETUP_RAILWAY.md dettagliato
17. README_SETUP_LOCAL.md dettagliato
18. `docs/ARCHITECTURE.md`
19. `docs/LANGCHAIN_GUIDE.md`
20. `docs/EXERCISES.md` con esercizi progressivi
21. `docs/TROUBLESHOOTING.md`

---

## 🚀 OUTPUT FINALE ATTESO

Repository completa con:
1. **Bot funzionante** su Railway e locale (polling)
2. **Documentazione completa** in italiano per neofiti
3. **Codice didattico** pesantemente commentato
4. **research.md** con analisi tecnica completa
5. **Esercizi progressivi** per apprendimento autonomo
6. **Setup guidato** per studenti (deploy 10-15 minuti)

Gli studenti potranno:
- ✅ Fork repository e deploy su Railway
- ✅ Configurare API keys in Environment Variables (Railway) o .env (locale)
- ✅ Modificare prompts senza toccare logica
- ✅ Caricare documenti PDF/DOCX/TXT via Telegram
- ✅ Fare query RAG con citazioni automatiche
- ✅ Usare web search per info aggiornate
- ✅ Processare immagini con Vision
- ✅ Generare risposte audio con TTS
- ✅ Sperimentare con parametri LangChain (temperature, top_k, etc.)
- ✅ Estendere bot con nuovi tools custom
- ✅ Capire flow LangChain Agent ReAct pattern

---

## 📝 NOTE FINALI IMPLEMENTAZIONE

1. **Consulta sempre `research.md`** per decisioni tecniche critiche
2. **Commenta abbondantemente** pensando a studenti neofiti
3. **Usa emoji nei log** per rendere output comprensibile
4. **Test su Railway** prima di considerare completo
5. **Errori devono essere user-friendly** su Telegram
6. **Ogni file deve essere standalone comprensibile** con docstring chiara
7. **Priorità: didattica > performance** (codice chiaro > codice ottimizzato)
8. **README.md è la prima impressione** - deve invogliare a provare

## ⚙️ LIMITAZIONI RAILWAY HOBBY PLAN

**Risorse per servizio:**
- RAM: 0.5 GB massimo
- vCPU: 1 vCPU
- Storage: 0.5 GB per volumes
- Costo: $5/mese con $5 di crediti inclusi

**Implicazioni per il progetto:**
- Limitare caricamento documenti a ~10-15 PDF medi (considerando RAM constraints)
- Ottimizzare uso memoria in ChromaDB
- Monitorare uso risorse con comando /stats
- Considerare cleanup periodico documenti vecchi se si raggiungono i limiti

---

**Implementa l'intero progetto seguendo queste specifiche. Inizia da `main.py` e procedi in ordine logico di dipendenze: config → langchain_core → telegram components → rag components → llm components → utils → documentazione.**