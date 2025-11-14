# 🤖 Bot Telegram Educativo con RAG e LangChain

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.3.x-green)
![Tempo Setup](https://img.shields.io/badge/Setup-15min-orange)
![Difficoltà](https://img.shields.io/badge/Difficolt%C3%A0-Facile-brightgreen)
![Licenza](https://img.shields.io/badge/Licenza-MIT-blue)

Crea il tuo **bot Telegram intelligente** che risponde usando documenti che carichi tu, cerca sul web, analizza immagini e genera audio! 🚀
Se hai aperto questo file da Visual Studio Code premi (Ctrl+Shift+V) per una migliore visione

**Perfetto per il tuo primo progetto con AI, Python e LangChain.**

---

## 📚 Cosa imparerai

- 🧠 **RAG (Retrieval-Augmented Generation)**: Il bot legge i tuoi documenti e risponde basandosi su di essi
- 🤖 **LangChain Agents**: Intelligenza artificiale che decide autonomamente quale strumento usare
- 🔍 **Web Search**: Cerca informazioni aggiornate online
- 👁️ **Vision AI**: Analizza immagini che gli invii
- 🔊 **Text-to-Speech**: Genera risposte vocali
- 💾 **Vector Database**: Salva e recupera documenti con ChromaDB

---

## 🎯 Setup Rapido (15 minuti)

### ✅ Checklist

- [ ] **Step 1**: Crea bot Telegram e ottieni token *(5 min)*
- [ ] **Step 2**: Personalizza la personalità del bot *(2 min)*
- [ ] **Step 3**: Configura API keys *(3 min)*
- [ ] **Step 4**: Crea ambiente virtuale e installa librerie *(3 min)*
- [ ] **Step 5**: Avvia il bot *(1 min)*
- [ ] **Step 6**: Carica documenti e inizia a chattare! *(1 min)*

---

## 📱 Step 1: Crea il Bot Telegram (5 min)

Devi ottenere **due informazioni** da Telegram:
1. **Bot Token** - per far funzionare il bot
2. **User ID** - per essere admin del bot

### 📖 Guide PDF

Trovi le guide complete nella cartella `how_to_telegram/`:

- 📄 **`1_Creazione_telegram_bot.pdf`** - Come creare il bot con @BotFather
- 📄 **`2_ID_Utente.pdf`** - Come ottenere il tuo User ID

**In breve:**

1. Apri Telegram e cerca **@BotFather**
2. Invia `/newbot` e segui le istruzioni
3. Copia il **token** che ti dà (tipo: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. Cerca **@userinfobot** e invia `/start` per ottenere il tuo **User ID**

✅ **Hai il token e lo user ID? Perfetto, andiamo avanti!**

---

## ✏️ Step 2: Personalizza il Bot (2 min)

Prima di avviare il bot, personalizza la sua **personalità**!

### 📝 Modifica `prompts.py`

Apri il file `prompts.py` e trova `SYSTEM_PROMPT`. Qui puoi scrivere quello che vuoi!

**Esempi:**

```python
# 👨‍🍳 Chef Esperto (per ricette)
SYSTEM_PROMPT = """
Sei uno chef stellato italiano esperto di cucina casalinga.
Quando gli utenti ti chiedono ricette, suggerisci piatti creativi usando
gli ingredienti che hanno a disposizione (che troverai nei documenti caricati).
Dai consigli pratici, dosaggi precisi e tempi di cottura.
Sii cordiale e usa emoji culinarie! 👨‍🍳🍝
"""

# 💪 Personal Trainer
SYSTEM_PROMPT = """
Sei un personal trainer motivante e professionale.
Aiuti le persone a raggiungere i loro obiettivi fitness consultando
schede di allenamento e piani nutrizionali nei documenti caricati.
Sii energico, positivo e dai consigli pratici! 💪🏋️
"""

# 📚 Tutor Scolastico
SYSTEM_PROMPT = """
Sei un tutor paziente che aiuta studenti a studiare.
Rispondi a domande basandoti sui materiali didattici caricati.
Spiega concetti complessi in modo semplice, fai esempi pratici.
Sii incoraggiante e chiedi se hanno capito! 📚✨
"""

# 🎮 Gaming Buddy
SYSTEM_PROMPT = """
Sei un esperto di videogiochi appassionato.
Aiuti i giocatori consultando guide, walkthrough e strategie nei documenti.
Dai consigli tattici, suggerisci build e combo.
Usa linguaggio gaming e emoji! 🎮🔥
"""
```

**Sii originale!** Inventa la personalità che preferisci 🎨

---

## 🔑 Step 3: Configura le API Keys (3 min)

### 📄 Trova il file `.env`

Nella cartella del progetto c'è già un file `.env` con la chiave OpenAI configurata.

**Tu devi solo aggiungere:**

1. **`TELEGRAM_BOT_TOKEN`** - Token che hai ottenuto da @BotFather
2. **`ADMIN_USER_IDS`** - Il tuo User ID da @userinfobot
3. **`TAVILY_API_KEY`** - Per web search (vedi sotto come ottenerla)

### 🔧 Come modificare `.env`

Apri `.env` con un editor di testo e compila così:

```env
# Il tuo bot token (da @BotFather)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Il tuo user ID (da @userinfobot)
ADMIN_USER_IDS=987654321

# Tavily per web search (vedi sotto)
TAVILY_API_KEY=tvly-xxxxxxxxxxxxx

# OpenAI è già configurata ✅
OPENAI_API_KEY=sk-proj-... (già presente)
```

### 🔍 Ottieni Tavily API Key (Gratis!)

Tavily permette al bot di cercare su internet:

1. Vai su [tavily.com](https://tavily.com)
2. Registrati (è gratis!)
3. Copia la API key dalla dashboard
4. Incollala nel `.env`

**Piano Free**: 1000 ricerche al mese (più che sufficiente!)

### ⚙️ Opzionale: Personalizza Altro

Nel `.env` puoi anche modificare (opzionale):

```env
# Cambia modello GPT (default: gpt-4o-mini)
LLM_MODEL=gpt-4o

# Creatività risposte (0.0 = preciso, 1.0 = creativo)
LLM_TEMPERATURE=0.7

# Voce per audio (alloy, echo, fable, onyx, nova, shimmer)
TTS_VOICE=alloy
```

---

## 💻 Step 4: Crea Virtual Environment e Installa Librerie (3 min)

### 📂 Apri il Terminal in VSCode

1. Apri la cartella del progetto in **VSCode**
2. Vai su **Terminal** → **Nuovo Terminale** (oppure <kbd>Ctrl</kbd> + <kbd>`</kbd>)
3. Dovresti vedere il path della cartella del progetto

### 🐍 Verifica quale comando Python usare

Prova uno di questi comandi (dipende dal tuo sistema):

| Sistema Operativo | Comandi da provare |
|-------------------|-------------------|
| **Windows** | `python --version` o `py --version` |
| **Mac/Linux** | `python3 --version` o `python --version` |

✅ **Se vedi** `Python 3.11.x` o superiore, sei a posto!

**Useremo il comando che ha funzionato** (es: `python`, `python3` o `py`)

---

### 📦 Crea e Attiva Virtual Environment

**Perché?** Per mantenere le librerie del progetto separate dal resto del sistema.

#### 🪟 Windows

```bash
# 1. Crea virtual environment (usa python, python3 o py)
python -m venv .venv

# 2. Attiva virtual environment
.venv\Scripts\activate

# ✅ Se vedi (.venv) davanti al path, è attivato!
```

#### 🍎 Mac/Linux

```bash
# 1. Crea virtual environment (usa python3 o python)
python3 -m venv .venv

# 2. Attiva virtual environment
source .venv/bin/activate

# ✅ Se vedi (.venv) davanti al path, è attivato!
```

**Esempio di cosa dovresti vedere:**

```
Prima:  C:\Users\tuonome\progetto>
Dopo:   (.venv) C:\Users\tuonome\progetto>
         ↑ Questo indica che è attivo!
```

---

### 📚 Installa le Librerie

**Ora installiamo tutto quello che serve** (ci vorranno 1-2 minuti):

#### 🪟 Windows

```bash
pip install -r requirements.txt
```

#### 🍎 Mac/Linux

```bash
pip3 install -r requirements.txt
```

**📊 Vedrai scorrere tante righe** - è normale! L'installazione è completa quando rivedi il path del terminal.

**⏱️ Tempo stimato:** 1-3 minuti (dipende dalla connessione)

---

### ⚠️ Problemi Comuni

| Problema | Soluzione |
|----------|-----------|
| ❌ `python: command not found` | Prova `python3` o `py` invece di `python` |
| ❌ `Permission denied` su Mac/Linux | Aggiungi `sudo` davanti al comando |
| ❌ `pip: command not found` | Prova `pip3` invece di `pip` |
| ❌ Virtual env non si attiva | Su Windows prova: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |

---

## 🚀 Step 5: Avvia il Bot (1 min)

**Siamo pronti!** Adesso avviamo il bot:

#### 🪟 Windows

```bash
python main.py
```

#### 🍎 Mac/Linux

```bash
python3 main.py
```

### ✅ Cosa dovresti vedere

Se tutto è andato bene vedrai:

```
🤖 Telegram AI Bot con RAG
✅ Tutte le API keys configurate correttamente!
✅ Virtual environment attivo
📊 ChromaDB inizializzato (0 documenti)
🚀 Bot avviato in modalità polling!
✅ Bot pronto a ricevere messaggi!
```

**🎉 Il bot è ATTIVO!** Puoi iniziare a chattare con lui su Telegram!

### ⚠️ Problemi?

| Problema | Soluzione |
|----------|-----------|
| ❌ `TELEGRAM_BOT_TOKEN not found` | Controlla che il `.env` sia compilato correttamente |
| ❌ `OPENAI_API_KEY invalid` | Verifica la chiave OpenAI nel `.env` |
| ❌ `Module not found` | Hai attivato il virtual environment? Vedi `(.venv)` nel terminal? |
| ❌ Emoji strani su Windows | Normale! Il bot funziona comunque. Per fixare: `chcp 65001` prima di `python main.py` |

---

## 💬 Step 6: Usa il Bot su Telegram!

### 🎯 Primi Passi

1. **Apri Telegram** e cerca il tuo bot (il nome che hai scelto)
2. **Invia** `/start` - Riceverai il benvenuto admin! 🎉
3. **Prova questi comandi:**

| Comando | Cosa fa |
|---------|---------|
| `/help` | Mostra tutti i comandi disponibili |
| Scrivi `Ciao!` | Il bot ti risponde (usa conoscenza generale GPT) |
| `/voice_on` | Attiva risposte vocali (audio MP3) |
| `/voice_off` | Disattiva audio |
| `/clear` | Cancella cronologia conversazione |

---

## 📄 Step 7: Carica Documenti (RAG in azione!)

**Qui succede la magia!** 🪄

Il bot può leggere **documenti che carichi tu** e rispondere basandosi su di essi.

### 📤 Come Caricare Documenti

1. **Invia** `/add_doc` al bot
2. **Carica un file**: PDF, DOCX o TXT
3. **Aspetta** - Il bot processa il documento (chunking + embeddings)
4. **Conferma** - Vedrai `✅ Documento aggiunto con successo!`

**Formati supportati:**
- 📕 PDF (`.pdf`)
- 📘 Word (`.docx`)
- 📃 Testo (`.txt`)

### 🔍 Gestisci Documenti

| Comando | Cosa fa |
|---------|---------|
| `/list_docs` | Mostra tutti i documenti caricati |
| `/delete_doc <id>` | Elimina un documento per ID |
| `/stats` | Statistiche: quanti doc, chunks, memoria usata |

### 💡 Esempi Pratici

**Scenario: Chef Bot 👨‍🍳**

1. Carica un PDF con **100 ricette italiane**
2. Chiedi: *"Ho pasta, pomodoro e basilico. Cosa posso cucinare?"*
3. Il bot cerca nelle ricette e suggerisce quelle adatte!

**Scenario: Study Bot 📚**

1. Carica le **dispense del corso** (PDF)
2. Chiedi: *"Spiegami il teorema di Pitagora"*
3. Il bot risponde basandosi sulle dispense!

**Scenario: Gaming Bot 🎮**

1. Carica **guide e walkthrough** (PDF/TXT)
2. Chiedi: *"Come sconfiggo il boss del livello 5?"*
3. Il bot consulta la guida e ti dice come fare!

---

## 🎨 Esempi di Personalizzazione

### 1. 👨‍🍳 Chef Bot - Consigliere Ricette

**Setup:**

1. **Modifica `prompts.py`:**
```python
SYSTEM_PROMPT = """
Sei uno chef italiano esperto in cucina casalinga.
Consulta il ricettario caricato e suggerisci piatti in base agli ingredienti
che l'utente ha a disposizione. Dai dosaggi, tempi e consigli pratici.
Sii creativo, cordiale e usa emoji! 👨‍🍳🍝
"""
```

2. **Carica documenti:**
   - `ricette_italiane.pdf`
   - `ricette_vegetariane.pdf`
   - `dolci_facili.pdf`

3. **Usa il bot:**
   - *"Ho uova, farina e zucchero"* → Suggerisce torta, pancake, crêpes
   - *"Ricetta carbonara autentica?"* → Trova ricetta nel PDF e la spiega
   - *"Cosa posso fare con melanzane?"* → Suggerisce parmigiana, pasta alla norma, etc.

---

### 2. 💪 Personal Trainer Bot

**Setup:**

1. **Modifica `prompts.py`:**
```python
SYSTEM_PROMPT = """
Sei un personal trainer motivante e professionale.
Consulta le schede di allenamento e i piani nutrizionali caricati.
Aiuta gli utenti a raggiungere i loro obiettivi fitness con consigli pratici.
Sii energico e positivo! 💪🏋️
"""
```

2. **Carica documenti:**
   - `scheda_palestra_principianti.pdf`
   - `piano_nutrizionale.pdf`
   - `esercizi_casa.pdf`

3. **Usa il bot:**
   - *"Voglio aumentare massa muscolare"* → Suggerisce scheda e alimentazione
   - *"Esercizi per addominali?"* → Consulta i PDF e spiega esercizi
   - *"Cosa mangiare prima dell'allenamento?"* → Risponde dal piano nutrizionale

---

### 3. 📚 Tutor Scolastico

**Setup:**

1. **Modifica `prompts.py`:**
```python
SYSTEM_PROMPT = """
Sei un tutor paziente che aiuta studenti a studiare.
Consulta i materiali didattici caricati e spiega concetti in modo semplice.
Fai esempi pratici e verifica che lo studente abbia capito. 📚✨
"""
```

2. **Carica documenti:**
   - `dispense_matematica.pdf`
   - `appunti_storia.pdf`
   - `grammatica_italiana.pdf`

3. **Usa il bot:**
   - *"Spiegami le equazioni di secondo grado"* → Spiega dalla dispensa
   - *"Chi era Napoleone?"* → Risponde dagli appunti di storia
   - *"Differenza tra che e cui?"* → Consulta la grammatica

---

### 4. 🏢 Assistant Aziendale

**Setup:**

1. **Modifica `prompts.py`:**
```python
SYSTEM_PROMPT = """
Sei un assistente aziendale che conosce procedure, policy e documentazione interna.
Aiuta i dipendenti a trovare informazioni velocemente consultando i documenti caricati.
Sii professionale, preciso e cita sempre la fonte. 📊💼
"""
```

2. **Carica documenti:**
   - `manuale_dipendente.pdf`
   - `policy_ferie.pdf`
   - `procedura_rimborsi.pdf`

3. **Usa il bot:**
   - *"Come richiedere le ferie?"* → Spiega la procedura dal manuale
   - *"Posso farmi rimborsare il taxi?"* → Consulta policy rimborsi
   - *"Orari ufficio?"* → Trova info nel manuale dipendente

---

### 5. 🎓 Q&A Bot per Eventi/Corsi

**Setup:**

1. **Modifica `prompts.py`:**
```python
SYSTEM_PROMPT = """
Sei l'assistente virtuale del corso [NOME CORSO].
Rispondi a domande su programma, orari, docenti e materiali consultando i documenti.
Sii cordiale e preciso! 🎓
"""
```

2. **Carica documenti:**
   - `programma_corso.pdf`
   - `calendario_lezioni.pdf`
   - `FAQ_studenti.pdf`

3. **Usa il bot:**
   - *"Quando è la prossima lezione?"* → Controlla calendario
   - *"Chi è il docente di Python?"* → Info dal programma
   - *"Come accedere alle registrazioni?"* → Risposta dalle FAQ

---

## ❓ FAQ - Domande Frequenti

### 🤔 "Il bot non risponde su Telegram"

**Controlla:**
- ✅ Il terminal con `python main.py` è ancora aperto?
- ✅ Vedi il messaggio `Bot pronto a ricevere messaggi!`?
- ✅ Il `TELEGRAM_BOT_TOKEN` nel `.env` è corretto?
- ✅ Hai cercato il bot giusto su Telegram?

**Soluzione:** Riavvia il bot con `python main.py` (dopo aver attivato `.venv`)

---

### 🤔 "Errore: Module not found"

**Causa:** Virtual environment non attivato o librerie non installate.

**Soluzione:**
1. Verifica che vedi `(.venv)` nel terminal
2. Se non c'è, attiva: `.venv\Scripts\activate` (Win) o `source .venv/bin/activate` (Mac)
3. Reinstalla: `pip install -r requirements.txt`

---

### 🤔 "Il bot non trova informazioni nei documenti"

**Cause possibili:**
- Il documento non contiene quella informazione
- Il chunk size è troppo piccolo (pezzi di testo troppo corti)
- Il RAG top-K è troppo basso (recupera pochi chunks)

**Soluzione:**
1. Verifica che il documento sia caricato: `/list_docs`
2. Prova a riformulare la domanda in modo più specifico
3. (Avanzato) Modifica `RAG_TOP_K` nel `.env` (es: da 8 a 15)

---

### 🤔 "Quanto costa OpenAI?"

**Stima per uso educativo:**
- **Embeddings** (caricare documenti): ~$0.02 per 1M tokens (one-time)
- **Chat**: ~$0.15 input + $0.60 output per 1M tokens
- **TTS Audio** (opzionale): ~$15 per 1M caratteri ⚠️ COSTOSO!

**Esempio pratico:**
- Carichi 50 pagine PDF: ~$0.10
- 100 messaggi chat: ~$0.05-0.10
- **Totale mensile**: $3-7 per uso moderato

💡 **Consiglio:** Disattiva TTS (`/voice_off`) per risparmiare!

---

### 🤔 "Il bot può cercare su internet?"

**Sì!** Se hai configurato `TAVILY_API_KEY`.

Il bot decide **automaticamente** quando usare:
- 🧠 **RAG** (documenti caricati) per info specifiche nei tuoi file
- 🌐 **Web Search** (Tavily) per info aggiornate online
- 💭 **Conoscenza GPT** per domande generali

**Esempio:**
- *"Chi ha vinto le elezioni 2024?"* → Web search (info recente)
- *"Ricetta carbonara nel mio ricettario?"* → RAG (documenti)
- *"Capitale della Francia?"* → Conoscenza GPT diretta

---

### 🤔 "Posso usare il bot con i miei amici?"

**Sì!** Ci sono due modi:

**Opzione 1: Tutti utenti normali**
- I tuoi amici possono chattare col bot
- **Non** possono caricare/eliminare documenti (solo admin)

**Opzione 2: Aggiungi altri admin**
- Modifica `.env`: `ADMIN_USER_IDS=tuo_id,amico_id1,amico_id2`
- Gli admin possono gestire documenti

---

### 🤔 "Come faccio a spegnere il bot?"

**Nel terminal** dove sta girando `python main.py`:
- **Windows/Mac/Linux**: <kbd>Ctrl</kbd> + <kbd>C</kbd>

Il bot si spegne gracefully (salva tutto prima di uscire).

---

### 🤔 "Posso usare il bot offline?"

**No**, il bot richiede:
- ✅ Connessione internet (per OpenAI API e Telegram)
- ✅ Telegram token valido
- ✅ OpenAI API key valida

**Ma:** I documenti e la conversazione sono salvati **localmente** nella cartella `data/`.

---

## 🛠️ Troubleshooting Avanzato

### Problema: ChromaDB SQLite Error

**Sintomo:**
```
sqlite3.OperationalError: unable to open database file
```

**Causa:** Versione SQLite vecchia (su Railway o sistemi Linux old)

**Soluzione:** Il workaround è già incluso in `config.py`, ma se persiste:

```bash
pip install pysqlite3-binary
```

---

### Problema: Emoji non visualizzate su Windows

**Sintomo:** Vedi caratteri strani tipo `?????` invece di emoji

**Causa:** Encoding di default del terminal Windows

**Soluzione:**

```bash
# Prima di eseguire main.py
chcp 65001

# Poi avvia normalmente
python main.py
```

**Nota:** Il bot funziona comunque! È solo un problema visivo nel terminal.

---

### Problema: "Too many requests" da OpenAI

**Sintomo:**
```
openai.RateLimitError: Rate limit exceeded
```

**Causa:** Hai superato il rate limit OpenAI (messaggi troppo velocemente)

**Soluzione:**
1. Aspetta 1 minuto
2. Se persiste, controlla credito account OpenAI
3. (Avanzato) Aggiungi rate limiting nel codice

---

### Problema: Bot lentissimo a rispondere

**Possibili cause:**
1. **Troppi documenti caricati** → Il bot cerca in troppi chunks
2. **File troppo grandi** → Chunking lento
3. **RAG_TOP_K troppo alto** → Recupera troppi chunks

**Soluzioni:**
1. Riduci `RAG_TOP_K` nel `.env` (es: da 15 a 5)
2. Elimina documenti non necessari: `/delete_doc <id>`
3. Ottimizza `CHUNK_SIZE` nel `.env` (prova 500-800)

---

### Problema: Virtual environment non si attiva su Windows

**Sintomo:**
```
cannot be loaded because running scripts is disabled on this system
```

**Causa:** ExecutionPolicy di PowerShell restrittiva

**Soluzione:**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Poi riprova: `.venv\Scripts\activate`

---

## 📂 Struttura del Progetto

**Cosa c'è nella cartella?**

```
develhope_telegram_bot/
│
├── 📄 main.py                       # ⭐ ESEGUI QUESTO per avviare il bot
├── ⚙️ config.py                     # Configurazioni (temperature, chunk_size, etc.)
├── 💬 prompts.py                    # ⭐ MODIFICA QUI la personalità del bot
├── 🧠 bot_engine.py                 # LangChain + RAG + Agent (cuore del bot)
├── 📱 telegram_messages.py          # Messaggi Telegram (benvenuto, errori, etc.)
│
├── 📦 requirements.txt              # Lista librerie da installare
├── 🔐 .env                          # ⭐ API Keys (da compilare)
├── 📝 .env.example                  # Template per .env
├── 🚫 .gitignore                    # File ignorati da git
│
├── 📂 src/                          # Codice sorgente modulare
│   ├── telegram/                    # Bot Telegram
│   │   ├── handlers.py              # Gestione comandi (/start, /add_doc, etc.)
│   │   ├── auth.py                  # Controllo permessi admin
│   │   └── message_processor.py    # Processing messaggi utente
│   │
│   ├── rag/                         # Sistema RAG
│   │   ├── vector_store.py          # ChromaDB (database vettoriale)
│   │   └── document_processor.py   # Caricamento PDF/DOCX/TXT
│   │
│   ├── llm/                         # AI Models
│   │   ├── audio.py                 # Text-to-Speech (OpenAI TTS)
│   │   └── image_processor.py      # Vision (GPT-4o analisi immagini)
│   │
│   └── utils/                       # Utility
│       ├── logger.py                # Logging (salva log in file)
│       └── helpers.py               # Funzioni helper
│
├── 📂 how_to_telegram/              # ⭐ GUIDE PDF
│   ├── 1_Creazione_telegram_bot.pdf
│   └── 2_ID_Utente.pdf
│
├── 📂 docs/                         # Documenti extra (programma corso, etc.)
│
└── 📂 data/                         # ⚠️ AUTO-GENERATO (non committare su git!)
    ├── vectordb/                    # Database ChromaDB
    ├── documents/                   # File caricati
    └── conversations/               # Backup chat (se abilitato)
```

### 🎯 File Chiave per Studenti

| File | Cosa fa | Devi modificarlo? |
|------|---------|-------------------|
| `main.py` | Avvia il bot | ❌ No |
| `prompts.py` | Personalità e comportamento bot | ✅ **Sì!** Personalizza qui |
| `.env` | API keys e configurazioni | ✅ **Sì!** Compila con le tue keys |
| `config.py` | Parametri avanzati (temperature, chunk_size) | ⚙️ Opzionale |
| `bot_engine.py` | Logica LangChain/RAG | 🧠 Avanzato (esercizi) |

---

## 🚀 Come Funziona (Architettura Semplificata)

```
         Tu su Telegram 💬
                ↓
         [Telegram Bot]
                ↓
        [Message Processor]
                ↓
     [LangChain Agent 🤖] ← Decide quale strumento usare
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
[📚 RAG]   [🌐 Web]    [💭 GPT]
(Docs)    (Tavily)   (Direct)
    ↓           ↓           ↓
    └───────────┼───────────┘
                ↓
         [Risposta generata]
                ↓
         ┌──────┴──────┐
         ↓             ↓
    [📝 Testo]    [🔊 Audio]
      (sempre)    (se /voice_on)
         ↓             ↓
    Risposta su Telegram ✅
```

### 📖 Spiegazione:

1. **Tu scrivi** un messaggio al bot su Telegram
2. **Message Processor** riceve il messaggio
3. **LangChain Agent** (ReAct pattern) **decide** autonomamente:
   - 📚 Usare **RAG** se la risposta è nei documenti
   - 🌐 Usare **Web Search** se serve info aggiornata
   - 💭 Rispondere direttamente con **conoscenza GPT**
4. **Genera la risposta**:
   - 📝 Sempre testo
   - 🔊 Anche audio se hai fatto `/voice_on`
5. **Ti risponde** su Telegram!

---

## 📚 Approfondimenti

### 🧠 Cos'è il RAG?

**RAG = Retrieval-Augmented Generation**

Invece di fare domande "a vuoto" a GPT, il bot:
1. **Recupera** pezzi di documenti rilevanti (retrieval)
2. **Augmenta** il prompt con questi documenti
3. **Genera** la risposta basandosi sui documenti

**Vantaggi:**
- ✅ Risposte basate su **tuoi dati privati**
- ✅ Info **aggiornate** (non limitate al training di GPT)
- ✅ **Citazioni** (il bot dice da dove ha preso l'info)
- ✅ Meno **allucinazioni** (risposte inventate)

---

### 🤖 Cos'è LangChain Agent?

Un **Agent** è un LLM che può:
- **Decidere** autonomamente quali strumenti usare
- **Chiamare** funzioni/API in base al contesto
- **Ragionare** step-by-step (ReAct pattern)

**Esempio pratico:**

```
User: "Chi ha vinto le elezioni 2024 in USA?"

Agent reasoning:
1. Questa domanda richiede info aggiornate
2. Non è nei documenti caricati
3. → USO WEB SEARCH (Tavily)
4. Trovo risultato online
5. → Rispondo all'utente
```

**Senza Agent:** Il bot risponderebbe sempre allo stesso modo, senza scegliere lo strumento giusto.

---

### 🗄️ Cos'è ChromaDB?

**ChromaDB** è un **vector database** che:
- Trasforma testi in **embeddings** (vettori numerici)
- Salva questi vettori
- Fa **similarity search** (trova testi simili)

**Esempio:**

```
Documento: "La carbonara si fa con guanciale, uova, pecorino"
Embedding: [0.23, -0.45, 0.87, ..., 0.12] (1536 numeri)

Query: "Ingredienti carbonara?"
Embedding Query: [0.25, -0.43, 0.89, ..., 0.11]

ChromaDB trova documenti con embedding SIMILI → Risposta precisa!
```

---

### 🎓 Esercizi per Imparare

#### Livello 1: Principiante 🟢

- [ ] Modifica `LLM_TEMPERATURE` e osserva come cambiano le risposte
- [ ] Cambia `RAG_TOP_K` (1, 5, 10) e vedi quali risultati ottieni
- [ ] Carica 3 documenti PDF diversi e fai domande su ciascuno

#### Livello 2: Intermedio 🟡

- [ ] Personalizza `SYSTEM_PROMPT` per 3 casi d'uso diversi
- [ ] Modifica `CHUNK_SIZE` e `CHUNK_OVERLAP` per ottimizzare retrieval
- [ ] Aggiungi messaggi custom in `telegram_messages.py`

#### Livello 3: Avanzato 🟠

- [ ] Implementa un nuovo tool custom in `bot_engine.py` (es: Calculator, Weather)
- [ ] Modifica la logica di retrieval per dare più peso a documenti recenti
- [ ] Aggiungi logging personalizzato per tracciare performance

#### Livello 4: Expert 🔴

- [ ] Implementa re-ranking dei risultati RAG
- [ ] Aggiungi feedback loop (l'utente valuta la risposta)
- [ ] Integra un secondo vector store (es: Pinecone) e confronta performance
- [ ] Implementa multi-agent system (più agent specializzati)

---

## 🌐 Risorse Utili

### 📖 Documentazione

- [LangChain Docs](https://python.langchain.com/docs/) - Guida completa LangChain
- [OpenAI Platform](https://platform.openai.com/docs) - API OpenAI
- [ChromaDB Docs](https://docs.trychroma.com/) - Vector database
- [python-telegram-bot](https://docs.python-telegram-bot.org/) - Telegram API

### 🎓 Tutorial

- [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)
- [ReAct Paper](https://arxiv.org/abs/2210.03629) - Come funzionano gli Agent
- [Prompt Engineering Guide](https://www.promptingguide.ai/)

### 💬 Community

- [LangChain Discord](https://discord.gg/langchain)
- [r/LangChain](https://reddit.com/r/langchain) - Reddit community

---

## 🎯 Prossimi Passi

**Hai finito il setup?** Ecco cosa fare ora:

1. ✅ **Sperimenta** - Carica documenti diversi, fai domande, testa i limiti
2. 🎨 **Personalizza** - Cambia prompts, temperature, chunk_size
3. 🧠 **Impara** - Leggi il codice in `bot_engine.py`, capisci come funziona
4. 🚀 **Estendi** - Aggiungi nuovi tool, migliora il RAG, crea funzionalità custom
5. 🌍 **Deploy online** - Segui `README_ONLINE.md` per mettere il bot su Railway

---

## 🤝 Contribuire

Questo è un progetto educativo open source!

**Vuoi contribuire?**
1. Fork il repository
2. Crea un branch per la tua feature
3. Fai le modifiche
4. Apri una Pull Request

**Idee di contributi:**
- Nuovi esempi di personalizzazione
- Tool custom interessanti
- Miglioramenti documentazione
- Fix bug
- Ottimizzazioni performance

---

## 📜 Licenza

MIT License - Libero di usare, modificare e distribuire.

---

## 🙏 Crediti

Sviluppato per il corso **[Develhope](https://develhope.co)** - Data Science & AI.

**Tecnologie utilizzate:**
- 🦜 [LangChain](https://langchain.com) - Orchestrazione AI
- 🤖 [OpenAI](https://openai.com) - GPT, Embeddings, Vision, TTS
- 🗄️ [ChromaDB](https://trychroma.com) - Vector Database
- 💬 [python-telegram-bot](https://python-telegram-bot.org/) - Telegram API
- 🔍 [Tavily](https://tavily.com) - Web Search API

---

<div align="center">

**Buono studio e buon coding! 🚀**

Hai domande? [Apri una Issue](../../issues) o chiedi nel forum del corso!

Made with ❤️ for aspiring AI developers

</div>
