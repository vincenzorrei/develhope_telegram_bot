# Bot Telegram Educativo con RAG

Bot Telegram intelligente con Retrieval-Augmented Generation (RAG), LangChain agents, e multimodalità (testo, immagini, audio).

**Progetto educativo** pensato per studenti al primo approccio con Python, AI e LangChain.

## Cosa fa questo bot?

- **RAG (Retrieval-Augmented Generation)**: Risponde a domande basandosi su documenti caricati (PDF, DOCX, TXT)
- **Web Search**: Cerca informazioni aggiornate su internet con Tavily
- **Vision AI**: Analizza immagini con GPT-4o Vision
- **Text-to-Speech**: Genera risposte vocali con OpenAI TTS
- **Memory**: Ricorda le conversazioni di ogni utente
- **Agent Intelligente**: Decide autonomamente quale strumento usare (ReAct pattern)

## Quick Start (10-15 minuti)

### Opzione 1: Railway (Consigliato per deploy in cloud)

Railway è una piattaforma cloud che permette di deployare il bot 24/7 senza dover lasciare il computer acceso.

**Setup Railway (passo-passo):**

1. **Fork questo repository** su GitHub
   - Vai su github.com e fai il fork del progetto
   - Questo crea una copia del codice nel tuo account

2. **Crea account su Railway**
   - Vai su [railway.app](https://railway.app)
   - Registrati con GitHub (consigliato)

3. **Crea nuovo progetto**
   - Dashboard Railway → "New Project"
   - Seleziona "Deploy from GitHub repo"
   - Scegli il repository che hai appena forkato

4. **Configura Environment Variables**
   - Railway → Project → Variables
   - Aggiungi queste variabili (⚠️ IMPORTANTE):
   ```
   TELEGRAM_BOT_TOKEN=il_tuo_token_da_BotFather
   OPENAI_API_KEY=sk-la_tua_key_openai
   TAVILY_API_KEY=tvly-la_tua_key_tavily
   ADMIN_USER_IDS=il_tuo_telegram_user_id
   ```

5. **Deploy automatico**
   - Railway rileva automaticamente `main.py` e installa dipendenze da `requirements.txt`
   - Il bot si avvia automaticamente dopo pochi minuti!
   - Controlla i log per verificare che sia partito correttamente

**Limiti Railway Hobby Plan ($5/mese con $5 crediti inclusi):**
- **RAM**: 512MB (sufficiente per 10-20 documenti PDF medi)
- **CPU**: Condivisa (sufficiente per uso moderato)
- **Storage**: Effimero (i documenti caricati potrebbero essere cancellati al redeploy - considera backup)
- **Esecuzione**: $0.000231/min (circa $10/mese per 24/7, ma crediti inclusi coprono uso base)

**Note tecniche:**
- ✅ Il workaround per SQLite vecchio è già implementato in `config.py`
- ✅ ChromaDB funziona out-of-the-box su Railway
- ⚠️ I file in `data/` sono effimeri - considera backup periodici dei documenti

[Guida dettagliata Railway →](README_SETUP_RAILWAY.md)

### Opzione 2: Locale

1. **Clone repository**:
   ```bash
   git clone <url-repo>
   cd develhope_telegram_bot
   ```

2. **Installa dipendenze** (richiede Python 3.11):
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura .env**:
   ```bash
   # Modifica il file .env esistente con le tue API keys
   # Aggiungi: TELEGRAM_BOT_TOKEN, ADMIN_USER_IDS, TAVILY_API_KEY
   ```

4. **Avvia il bot**:
   ```bash
   python main.py
   ```

[Guida dettagliata Setup Locale →](README_SETUP_LOCAL.md)

## Ottenere le API Keys

### Telegram Bot Token

1. Apri Telegram e cerca **@BotFather**
2. Invia `/newbot`
3. Segui le istruzioni per creare il bot
4. Copia il token che ti viene fornito
5. **Ottieni il tuo User ID**: Cerca **@userinfobot** e mandagli `/start`

### OpenAI API Key

1. Vai su [platform.openai.com](https://platform.openai.com)
2. Registrati/accedi
3. Vai in **API Keys** → **Create new secret key**
4. Copia la key (inizia con `sk-`)
5. **IMPORTANTE**: Aggiungi credito al tuo account (minimo $5)

### Tavily API Key (Web Search)

1. Vai su [tavily.com](https://tavily.com)
2. Registrati
3. Copia la API key dalla dashboard
4. **Free tier**: 1000 ricerche/mese gratis

## Comandi Disponibili

### Comandi Admin (solo per ADMIN_USER_IDS)

| Comando | Descrizione |
|---------|-------------|
| `/add_doc` | Carica un nuovo documento (PDF, DOCX, TXT) |
| `/list_docs` | Mostra tutti i documenti caricati |
| `/delete_doc <id>` | Elimina un documento per ID |
| `/stats` | Statistiche sistema (storage, documenti, utenti) |

### Comandi Utente (tutti possono usare)

| Comando | Descrizione |
|---------|-------------|
| `/start` | Messaggio di benvenuto |
| `/help` | Mostra aiuto comandi |
| `/clear` | Cancella cronologia conversazione |
| `/voice_on` | Attiva risposte vocali (TTS) |
| `/voice_off` | Disattiva risposte vocali |

### Messaggi Normali

- **Testo**: Invia una domanda normale → Il bot risponde usando RAG, web search o conoscenza generale
- **Immagini**: Invia un'immagine → GPT-4o Vision la analizza
- **Documenti**: Gli admin possono caricare PDF/DOCX/TXT per RAG

## Struttura Progetto

```
develhope_telegram_bot/
├── main.py                      # Entry point (esegui questo!)
├── config.py                    # Configurazione (MODIFICA QUI per sperimentare)
├── prompts.py                   # Prompt centralizzati (MODIFICA QUI per personalizzare)
├── bot_engine.py                # CUORE DIDATTICO - LangChain + RAG + Agent
├── telegram_messages.py         # Messaggi predefiniti del bot
│
├── requirements.txt             # Dipendenze Python
├── .env                         # API Keys (da compilare - gitignored)
├── .gitignore                   # File da ignorare in git
│
├── how_to_telegram/             # Guide PDF per setup Telegram
│   ├── 1_Creazione_telegram_bot.pdf
│   └── 2_ID_Utente.pdf
│
├── src/
│   ├── telegram/
│   │   ├── handlers.py          # Handler comandi e messaggi
│   │   ├── auth.py              # Decoratori autenticazione
│   │   ├── bot_setup.py         # Setup bot Telegram
│   │   └── message_processor.py # Processing messaggi
│   │
│   ├── rag/
│   │   ├── vector_store.py      # ChromaDB wrapper
│   │   ├── document_processor.py # Caricamento e chunking documenti
│   │   └── retriever.py         # Query e retrieval
│   │
│   ├── llm/
│   │   ├── audio.py             # OpenAI TTS
│   │   └── image_processor.py   # GPT-4o Vision
│   │
│   └── utils/
│       ├── logger.py            # Logging configurabile
│       ├── helpers.py           # Utility functions
│       ├── conversation_manager.py # Gestione memoria
│       ├── intelligent_memory_manager.py # Memory management avanzato
│       └── shared_clients.py    # Client condivisi (OpenAI, etc.)
│
└── data/                        # AUTO-GENERATO (gitignored)
    ├── vectordb/                # ChromaDB SQLite database
    ├── documents/               # File originali caricati
    └── conversations/           # Backup conversazioni
```

## Personalizzazione per Studenti

### 1. Modificare Parametri (config.py)

```python
# Sperimentare con temperature LLM (creatività)
LLM_TEMPERATURE = 0.7  # 0.0 = preciso, 1.0 = creativo

# Modificare quanti documenti recuperare
RAG_TOP_K = 3  # 1-10

# Cambiare dimensione chunks
CHUNK_SIZE = 800  # 300-2000 caratteri
```

### 2. Personalizzare Prompts (prompts.py)

```python
# Cambiare comportamento del bot
SYSTEM_PROMPT = """Sei un assistente..."""

# Modificare stile risposte RAG
RAG_QUERY_PROMPT = """..."""
```

### 3. Aggiungere Tools Custom (bot_engine.py)

Esempio: Aggiungere una calcolatrice

```python
def _setup_tools(self):
    tools = []

    # Tool calcolatrice
    calculator_tool = Tool(
        name="calculator",
        description="Esegue calcoli matematici. Input: espressione.",
        func=lambda x: str(eval(x))
    )
    tools.append(calculator_tool)

    return tools
```

Vedi **esercizi completi** in `bot_engine.py` (commenti finali)!

## Come Funziona (Architettura)

```
User Message (Telegram)
    ↓
Message Handler
    ↓
LangChain Agent (ReAct)
    ├─→ Tool 1: RAG Search (ChromaDB)
    ├─→ Tool 2: Web Search (Tavily)
    └─→ Direct Answer (LLM knowledge)
    ↓
Response Generation
    ├─→ Text (always)
    └─→ Audio (if voice_mode ON)
    ↓
Send to User
```

### RAG Pipeline Dettagliato

1. **Document Upload** (Admin):
   - Carica PDF/DOCX/TXT
   - Estrazione testo (pypdf/python-docx)
   - Chunking intelligente (RecursiveCharacterTextSplitter)
   - Generazione embeddings (OpenAI text-embedding-3-small)
   - Storage in ChromaDB

2. **Query** (User):
   - User invia domanda
   - Agent decide se usare RAG, web search, o risposta diretta
   - Se RAG: Similarity search in ChromaDB (top-K chunks)
   - Costruzione prompt augmented con documenti recuperati
   - LLM genera risposta basata su documenti
   - Citazioni fonti automatiche

## Troubleshooting

### Errore: "Module not found"

```bash
pip install -r requirements.txt
```

### Errore: "API key not configured"

Verifica .env (locale) o Environment Variables (Railway) contengano le keys.

### Bot non risponde

1. Verifica che il bot sia in esecuzione (`python main.py`)
2. Controlla i log per errori
3. Verifica che l'utente sia in ADMIN_USER_IDS se usa comandi admin

### ChromaDB SQLite Error (solo Railway o sistemi con SQLite vecchio)

Il workaround è già incluso in `config.py`. Se persiste:
```bash
pip install pysqlite3-binary
```

### Emoji non funzionano su Windows

Normale! Il bot funziona comunque. Per fix:
```bash
chcp 65001  # In cmd prima di eseguire
```

## FAQ

**Q: Quanto costa far funzionare il bot?**
A: Dipende dall'uso:
- **Embeddings**: ~$0.02 per 1M tokens (one-time per documento)
- **Chat**: ~$0.15 input + $0.60 output per 1M tokens
- **TTS** (opzionale): ~$15 per 1M caratteri (COSTOSO!)
- **Vision** (opzionale): ~$2.50-10 per 1M tokens

Stima: ~$5-10/mese per uso educativo moderato (senza TTS).

**Q: Posso usare modelli diversi da OpenAI?**
A: Sì! LangChain supporta molti provider (Anthropic, Cohere, HuggingFace, etc.). Modifica `config.py`.

**Q: ChromaDB vs altri vector databases?**
A: ChromaDB è ottimo per iniziare (zero config, local-first). Per produzione considera Pinecone, Weaviate, o Qdrant.

**Q: ReAct vs altri agent types?**
A: ReAct è ottimo per apprendimento (reasoning esplicito). Alternative: OpenAI Functions, Structured Chat, Plan-and-Execute.

**Q: Quanti documenti posso caricare?**
A: Su Railway Hobby Plan (0.5GB RAM): ~10-15 PDF medi. Per più documenti, considera upgrade a plan superiore o deploy locale. In locale: dipende dal tuo storage e RAM disponibile.

## Esercizi Progressivi

### Livello 1: Configurazione (Principiante)

- [ ] Modifica `LLM_TEMPERATURE` e osserva cambiamenti risposte
- [ ] Cambia `RAG_TOP_K` (1, 3, 5, 10) e confronta qualità
- [ ] Sperimenta con `CHUNK_SIZE` (300, 800, 1500)

### Livello 2: Prompts (Intermedio)

- [ ] Personalizza `SYSTEM_PROMPT` per dominio specifico (es: mate, storia)
- [ ] Modifica `RAG_QUERY_PROMPT` per cambiare stile citazioni
- [ ] Crea prompt custom per nuovi use case

### Livello 3: Tools (Avanzato)

- [ ] Aggiungi tool Calculator
- [ ] Integra Wikipedia API
- [ ] Crea tool Weather con OpenWeatherMap
- [ ] Implementa tool custom per il tuo caso d'uso

### Livello 4: Architecture (Expert)

- [ ] Implementa feedback loop in RAG
- [ ] Aggiungi re-ranking dei risultati
- [ ] Usa diversi agent types (Conversational, Structured)
- [ ] Implementa multi-agent system

Vedi esercizi dettagliati in `bot_engine.py`!

## Risorse Utili

### Documentazione

- [LangChain Docs](https://python.langchain.com/docs/)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [python-telegram-bot Docs](https://docs.python-telegram-bot.org/)

### Tutorial

- [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)

### Community

- [LangChain Discord](https://discord.gg/langchain)
- [r/LangChain](https://reddit.com/r/langchain)

## Contribuire

Questo è un progetto educativo open source! Contributi benvenuti:

1. Fork il repository
2. Crea branch per la tua feature (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri Pull Request

## Licenza

MIT License - vedi [LICENSE](LICENSE) file.

## Crediti

Sviluppato per il corso [Develhope](https://develhope.co) - Data Science & AI.

Tecnologie utilizzate:
- [LangChain](https://langchain.com) - Orchestrazione AI
- [OpenAI](https://openai.com) - LLM, Embeddings, TTS, Vision
- [ChromaDB](https://trychroma.com) - Vector Database
- [python-telegram-bot](https://python-telegram-bot.org/) - Telegram API
- [Tavily](https://tavily.com) - Web Search API

---

**Buono studio e buon coding! 🚀**

Per domande o supporto, apri una [Issue](../../issues) su GitHub.
