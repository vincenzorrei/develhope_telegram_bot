# Guida Completa all'Implementazione di un Sistema RAG con Memory

Questa guida spiega in dettaglio come implementare un sistema RAG (Retrieval-Augmented Generation) con supporto per la memoria conversazionale, basato sull'implementazione in `8 - React Docstore.ipynb`.

## Indice

1. [Introduzione al RAG](#introduzione-al-rag)
2. [Componenti Principali](#componenti-principali)
3. [Implementazione Step-by-Step](#implementazione-step-by-step)
4. [RAG con Memoria Conversazionale](#rag-con-memoria-conversazionale)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

## Introduzione al RAG

Il **RAG (Retrieval-Augmented Generation)** è una tecnica che combina:
- **Retrieval**: Recupero di informazioni rilevanti da una base di conoscenza
- **Generation**: Generazione di risposte usando un LLM con il contesto recuperato

Vantaggi:
- Accesso a conoscenze private/specifiche non presenti nel training del LLM
- Risposte basate su fonti verificabili
- Riduzione delle allucinazioni
- Aggiornamento della conoscenza senza riaddestramento

## Componenti Principali

Un sistema RAG completo richiede 6 componenti:

1. **LLM**: Modello linguistico per generare risposte
2. **Tools**: Strumenti per interagire con dati esterni
3. **Prompt Template**: Template per strutturare le richieste
4. **Parser**: Per processare gli output del LLM
5. **Memory**: Gestione della cronologia conversazionale
6. **Vector Store**: Database vettoriale per recupero semantico

## Implementazione Step-by-Step

### 1. Caricamento dei Documenti

```python
from langchain.document_loaders import DirectoryLoader

# Carica tutti i file .txt da una directory
loader = DirectoryLoader('docs', glob="*.txt", show_progress=True)
documents = loader.load()
```

**Note importanti:**
- `glob="*.txt"` filtra solo file di testo
- `show_progress=True` mostra l'avanzamento del caricamento
- Ogni documento mantiene metadata sulla fonte

### 2. Text Splitting

I documenti devono essere divisi in chunk più piccoli per:
- Migliorare la precisione del retrieval
- Rispettare i limiti di token del LLM
- Ottimizzare le performance di embedding

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,      # Dimensione massima del chunk
    chunk_overlap=100    # Overlap tra chunk consecutivi
)
splits = text_splitter.split_documents(documents)
```

**Parametri chiave:**
- `chunk_size=300`: Ogni chunk sarà di ~300 caratteri
- `chunk_overlap=100`: 100 caratteri di sovrapposizione per mantenere contesto

**Best practice per chunk_size:**
- Documenti tecnici: 500-1000 caratteri
- Testo narrativo: 300-500 caratteri
- FAQ/Q&A: 200-300 caratteri

### 3. Creazione del Vector Store

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# Crea un vector store locale con Chroma
vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=OpenAIEmbeddings()
)

# Converti in retriever
retriever = vectorstore.as_retriever()
```

**Cosa succede:**
1. Ogni chunk viene convertito in un vettore (embedding)
2. I vettori vengono memorizzati in Chroma (DB locale)
3. Il retriever permette ricerche semantiche

### 4. Configurazione del LLM

```python
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.1,  # Bassa temperatura per risposte più deterministiche
    api_key=os.getenv("openai_api_key")
)
```

**Note sulla temperatura:**
- `0.0-0.3`: Risposte precise e consistenti (ideale per RAG)
- `0.7-1.0`: Risposte più creative ma meno prevedibili

### 5. RAG Chain Base

```python
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain import hub

# Recupera un prompt standard per RAG
prompt = hub.pull("rlm/rag-prompt")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Crea la chain RAG
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)

# Utilizzo
response = rag_chain.invoke("La tua domanda qui")
```

**Come funziona:**
1. La domanda viene passata al retriever
2. Il retriever cerca i documenti più rilevanti
3. I documenti vengono formattati come contesto
4. Il prompt combina contesto + domanda
5. Il LLM genera la risposta
6. L'output viene parsato come stringa

## RAG con Memoria Conversazionale: Guida Completa

### Il Problema da Risolvere

Un sistema RAG base non gestisce conversazioni multi-turno. Considera questo scenario:

```
User: "Tra quali mezzi di trasporto è indeciso l'utente?"
Assistant: "L'utente è indeciso tra auto, scooter e moto."

User: "Qual è il vantaggio di quello scelto?"
Assistant: ❌ "Non ho informazioni su cosa sia stato scelto."
```

Il problema: la seconda domanda usa un **riferimento anaforico** ("quello scelto") che non ha senso senza il contesto conversazionale. Il retriever cerca documenti per "quello scelto" ma non trova nulla di rilevante.

### La Soluzione: History-Aware RAG

L'idea è creare un sistema che:
1. Analizza la cronologia conversazionale
2. Riformula domande ambigue in domande standalone
3. Usa la domanda riformulata per il retrieval
4. Genera risposte considerando sia il contesto recuperato che la storia

**Architettura:**
```
Query Utente + Chat History
         ↓
[STEP 1: Contestualizzazione]
    LLM riformula query
         ↓
Query Standalone
         ↓
[STEP 2: Retrieval]
    Vector Store Search
         ↓
Retrieved Documents
         ↓
[STEP 3: Generazione]
    LLM + Docs + History
         ↓
Risposta Finale
```

### Implementazione Passo-Passo

#### STEP 1: History Aware Retriever

Questo componente è responsabile di trasformare domande contestuali in domande standalone.

##### 1.1 Definire il Prompt di Contestualizzazione

```python
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Questo prompt istruisce l'LLM su come riformulare le domande
contextualization_prompt = """Given a chat history and the latest user question
which might reference context in the chat history, formulate a standalone question
which can be understood without the chat history. Do NOT answer the question,
just reformulate it if needed and otherwise return it as is.

EXAMPLES:
Chat History: [User: "Mi piacciono le moto", AI: "Ottima scelta!"]
Question: "Quali sono i vantaggi?"
Reformulated: "Quali sono i vantaggi delle moto?"

Chat History: [User: "Sto scegliendo tra auto e moto", AI: "Ho capito la tua indecisione"]
Question: "Cosa mi consigli?"
Reformulated: "Cosa mi consigli tra auto e moto?"

Chat History: []
Question: "Che tempo fa?"
Reformulated: "Che tempo fa?" (already standalone)
"""
```

**Cosa fa questo prompt:**
- Riceve la cronologia + domanda corrente
- Identifica riferimenti al contesto precedente
- Riformula sostituendo pronomi/riferimenti con nomi espliciti
- Se la domanda è già standalone, la restituisce invariata

##### 1.2 Creare il Template del Prompt

```python
# Questo è il template che verrà riempito con dati reali
contextualize_query_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualization_prompt),           # Istruzioni fisse
    MessagesPlaceholder("chat_history"),            # Slot per cronologia dinamica
    ("human", "{input}"),                           # Slot per domanda utente
])
```

**Componenti del template:**
1. **System Message**: Istruzioni per l'LLM (prompt di contestualizzazione)
2. **MessagesPlaceholder**: Container per messaggi storici variabili
3. **Human Message**: La domanda corrente dell'utente

##### 1.3 Creare l'History Aware Retriever

```python
# Assumi che llm e retriever siano già definiti (vedi sezioni precedenti)
history_aware_retriever = create_history_aware_retriever(
    llm,                            # LLM per riformulare
    retriever,                      # Retriever del vector store
    contextualize_query_prompt      # Prompt di contestualizzazione
)
```

**Cosa fa `create_history_aware_retriever`:**
1. Riceve input: `{"input": "domanda", "chat_history": [...]}`
2. Se `chat_history` è vuoto → passa direttamente `input` al retriever
3. Se `chat_history` ha messaggi:
   - Chiama LLM con prompt + storia + domanda
   - Ottiene domanda riformulata
   - Passa domanda riformulata al retriever
4. Restituisce documenti rilevanti

**Esempio pratico:**
```python
# Test del history aware retriever
from langchain_core.messages import HumanMessage, AIMessage

# Simula conversazione precedente
chat_history = [
    HumanMessage(content="Sto decidendo tra auto e moto"),
    AIMessage(content="Capisco, è una scelta importante. Che tipo di uso ne faresti?"),
    HumanMessage(content="Principalmente in città"),
    AIMessage(content="In città la moto offre grande manovrabilità")
]

# Domanda contestuale
query = "Quali sono gli svantaggi?"

# Il retriever riformula automaticamente
# "Quali sono gli svantaggi?" → "Quali sono gli svantaggi della moto in città?"
docs = history_aware_retriever.invoke({
    "input": query,
    "chat_history": chat_history
})

print(f"Documenti trovati: {len(docs)}")
for doc in docs:
    print(f"- {doc.page_content[:100]}...")
```

#### STEP 2: Question Answer Chain

Ora che abbiamo i documenti rilevanti, dobbiamo generare la risposta finale considerando:
- Documenti recuperati (context)
- Cronologia conversazionale (chat_history)
- Domanda corrente (input)

##### 2.1 Definire il Prompt di Risposta

```python
from langchain.chains.combine_documents import create_stuff_documents_chain

# Questo prompt guida la generazione della risposta
qa_system_prompt = """You are an assistant for question-answering tasks.

RULES:
1. Use the following pieces of retrieved context to answer the question
2. If you don't know the answer from the context, say "Non ho trovato informazioni sufficienti"
3. Use three sentences maximum and keep the answer concise
4. Reply in Italian
5. Be consistent with the conversation history

IMPORTANT: The chat history provides context about what has been discussed.
Use it to understand references in the current question, but base your answer on the retrieved context below.

CONTEXT:
{context}
"""
```

**Differenze rispetto al prompt base RAG:**
- Include riferimento esplicito alla chat history
- Istruisce l'LLM a essere coerente con la conversazione
- Chiarisce che la risposta deve basarsi sul contesto recuperato

##### 2.2 Creare il Template del Prompt

```python
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", qa_system_prompt),           # Istruzioni + slot {context}
    MessagesPlaceholder("chat_history"),    # Cronologia conversazione
    ("human", "{input}"),                   # Domanda corrente
])
```

**Flusso dei dati:**
```
{
    "context": "doc1\n\ndoc2\n\ndoc3",      # Inserito in qa_system_prompt
    "chat_history": [msg1, msg2, ...],       # Inserito come messaggi
    "input": "domanda utente"                # Inserito come human message
}
         ↓
[System: "You are an assistant... CONTEXT: doc1\n\ndoc2..."]
[Human: "messaggio1"]
[AI: "risposta1"]
[Human: "messaggio2"]
[AI: "risposta2"]
[Human: "domanda utente"]
         ↓
        LLM
         ↓
    Risposta
```

##### 2.3 Creare la Question Answer Chain

```python
# Questa chain prende documenti + storia e genera risposta
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
```

**Cosa fa `create_stuff_documents_chain`:**
1. Riceve documenti recuperati + chat_history + input
2. Formatta i documenti come stringa di contesto
3. Riempie il template del prompt
4. Chiama l'LLM
5. Restituisce la risposta

**Test della chain (standalone):**
```python
from langchain.docstore.document import Document

# Simula documenti recuperati
test_docs = [
    Document(page_content="La moto in città è agile ma pericolosa in caso di pioggia."),
    Document(page_content="L'auto offre protezione ma il traffico è un problema.")
]

# Test senza storia
response = question_answer_chain.invoke({
    "input": "Quali sono gli svantaggi della moto?",
    "context": test_docs,
    "chat_history": []
})

print(response)  # "La moto in città può essere pericolosa in caso di pioggia..."
```

#### STEP 3: Combinare Tutto nella RAG Chain Finale

Ora uniamo retrieval contestualizzato + generazione della risposta:

```python
from langchain.chains import create_retrieval_chain

# Questa è la chain completa che gestisce tutto il flusso
rag_chain = create_retrieval_chain(
    history_aware_retriever,      # STEP 1: riformula + recupera docs
    question_answer_chain         # STEP 2: genera risposta con docs
)
```

**Cosa fa `create_retrieval_chain`:**
```
Input: {"input": query, "chat_history": history}
         ↓
FASE 1: History Aware Retriever
    - Riformula query se necessario
    - Cerca nel vector store
    - Output: documenti rilevanti
         ↓
FASE 2: Question Answer Chain
    - Riceve: documenti + history + query
    - Genera risposta
    - Output: risposta finale
         ↓
Output: {
    "input": query originale,
    "chat_history": history,
    "context": documenti recuperati,
    "answer": risposta generata
}
```

#### STEP 4: Gestione della Conversazione

Ora implementiamo il loop conversazionale completo:

```python
from langchain_core.messages import HumanMessage, AIMessage

# 1. INIZIALIZZAZIONE
# Cronologia conversazione (vuota all'inizio)
chat_history = []

print("=== CONVERSAZIONE RAG CON MEMORIA ===\n")

# 2. PRIMA INTERAZIONE
question1 = "Tra quali mezzi di trasporto è indeciso l'utente?"
print(f"USER: {question1}")

response1 = rag_chain.invoke({
    "input": question1,
    "chat_history": chat_history  # [] vuoto per prima domanda
})

answer1 = response1["answer"]
print(f"ASSISTANT: {answer1}\n")
# Output: "L'utente è indeciso tra auto, scooter e moto."

# 3. AGGIORNAMENTO CRONOLOGIA
# IMPORTANTE: aggiungiamo sia domanda che risposta
chat_history.extend([
    HumanMessage(content=question1),
    AIMessage(content=answer1)
])

# Stato corrente chat_history:
# [
#   HumanMessage("Tra quali mezzi..."),
#   AIMessage("L'utente è indeciso tra auto, scooter e moto.")
# ]

# 4. SECONDA INTERAZIONE (con riferimento anaforico)
question2 = "Qual è il vantaggio di quello scelto?"
print(f"USER: {question2}")

response2 = rag_chain.invoke({
    "input": question2,
    "chat_history": chat_history  # Ora contiene la conversazione precedente
})

answer2 = response2["answer"]
print(f"ASSISTANT: {answer2}")
# Output: "Il vantaggio della moto è la sensazione di libertà e movimento..."

# 5. CONTINUA LA CONVERSAZIONE
chat_history.extend([
    HumanMessage(content=question2),
    AIMessage(content=answer2)
])

# Terza domanda
question3 = "E gli svantaggi?"
response3 = rag_chain.invoke({
    "input": question3,
    "chat_history": chat_history
})
print(f"\nUSER: {question3}")
print(f"ASSISTANT: {response3['answer']}")
```

**Output Esempio:**
```
=== CONVERSAZIONE RAG CON MEMORIA ===

USER: Tra quali mezzi di trasporto è indeciso l'utente?
ASSISTANT: L'utente è indeciso tra auto, scooter e moto.

USER: Qual è il vantaggio di quello scelto?
ASSISTANT: Il vantaggio della moto scelta è la sensazione di libertà e movimento,
con il cuore che accelera e la città che si apre come un labirinto da attraversare.

USER: E gli svantaggi?
ASSISTANT: Gli svantaggi della moto includono la pericolosità in caso di maltempo
e la mancanza di protezione rispetto all'auto.
```

**Cosa succede dietro le quinte nella seconda domanda:**

```
Input: "Qual è il vantaggio di quello scelto?"
Chat History: [user: "Tra quali...", ai: "indeciso tra auto, scooter e moto"]
         ↓
HISTORY AWARE RETRIEVER
    LLM analizza: "quello scelto" si riferisce alla moto (dalla storia)
    Riformula: "Qual è il vantaggio della moto scelta dall'utente?"
    Cerca nel vector store: documenti su vantaggi moto
    Trova: ["libertà", "movimento rapido", "attraversare traffico"]
         ↓
QUESTION ANSWER CHAIN
    Context: documenti su moto
    History: conversazione precedente
    Input: domanda originale
    Genera: "Il vantaggio della moto è..."
         ↓
Output: risposta contestualizzata
```

#### STEP 5: Recupero e Verifica delle Fonti

È fondamentale tracciare quali documenti hanno generato la risposta:

```python
# La risposta contiene i documenti utilizzati
print("\n=== FONTI UTILIZZATE ===")
for i, doc in enumerate(response2["context"], 1):
    print(f"\nFonte {i}:")
    print(f"  File: {doc.metadata.get('source', 'N/A')}")
    print(f"  Contenuto: {doc.page_content[:150]}...")

    # Altri metadata utili
    if 'page' in doc.metadata:
        print(f"  Pagina: {doc.metadata['page']}")
```

**Output:**
```
=== FONTI UTILIZZATE ===

Fonte 1:
  File: docs/monologo.txt
  Contenuto: Io voglio sentirmi guidare. Voglio che ogni curva sia una piccola vittoria,
  che ogni semaforo sia un momento di attesa prima di ripartire con il cuore...

Fonte 2:
  File: docs/monologo.txt
  Contenuto: Lo scooter è furbo, certo: pratico, ti porta al lavoro senza pensarci troppo.
  Io invece non cerco solo un mezzo di trasporto...
```

#### STEP 6: Implementazione di un Loop Interattivo

Per un chatbot completo:

```python
def run_rag_chatbot():
    """Chatbot RAG interattivo con memoria conversazionale"""
    chat_history = []

    print("=== RAG CHATBOT (digita 'exit' per uscire) ===\n")

    while True:
        # Input utente
        user_input = input("USER: ").strip()

        if user_input.lower() in ['exit', 'quit', 'esci']:
            print("Conversazione terminata.")
            break

        if not user_input:
            continue

        try:
            # Invoca RAG chain
            response = rag_chain.invoke({
                "input": user_input,
                "chat_history": chat_history
            })

            answer = response["answer"]
            print(f"ASSISTANT: {answer}\n")

            # Mostra fonti (opzionale)
            sources = set(doc.metadata.get('source', 'N/A')
                         for doc in response["context"])
            print(f"[Fonti: {', '.join(sources)}]\n")

            # Aggiorna cronologia
            chat_history.extend([
                HumanMessage(content=user_input),
                AIMessage(content=answer)
            ])

        except Exception as e:
            print(f"ERRORE: {e}\n")

    return chat_history

# Esegui chatbot
final_history = run_rag_chatbot()
```

### Gestione Avanzata della Cronologia

#### Limitare la Lunghezza della Cronologia

Per evitare token excess e costi elevati:

```python
MAX_HISTORY_LENGTH = 10  # Ultimi 5 scambi (10 messaggi)

def trim_history(history, max_length=MAX_HISTORY_LENGTH):
    """Mantieni solo gli ultimi N messaggi"""
    if len(history) > max_length:
        return history[-max_length:]
    return history

# Uso
chat_history = trim_history(chat_history)
response = rag_chain.invoke({
    "input": query,
    "chat_history": chat_history
})
```

#### Compressione della Cronologia

Per conversazioni molto lunghe, comprimi messaggi vecchi:

```python
from langchain.memory import ConversationSummaryMemory

# Crea memoria con riassunto automatico
memory = ConversationSummaryMemory(
    llm=llm,
    return_messages=True
)

# Aggiungi messaggi
memory.save_context(
    {"input": "Prima domanda"},
    {"output": "Prima risposta"}
)

# Recupera storia (riassunta se troppo lunga)
compressed_history = memory.load_memory_variables({})["history"]
```

### Debugging e Troubleshooting

#### Verificare la Riformulazione

```python
# Crea una versione standalone del history aware retriever per debugging
from langchain_core.runnables import RunnablePassthrough

debug_chain = (
    contextualize_query_prompt
    | llm
    | StrOutputParser()
)

# Test riformulazione
reformulated = debug_chain.invoke({
    "input": "E gli svantaggi?",
    "chat_history": [
        HumanMessage("Parlami delle moto"),
        AIMessage("Le moto sono veicoli a due ruote...")
    ]
})

print(f"Query originale: 'E gli svantaggi?'")
print(f"Query riformulata: '{reformulated}'")
# Output: "Quali sono gli svantaggi delle moto?"
```

#### Logging Dettagliato

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Ogni chiamata LLM verrà loggata
response = rag_chain.invoke({
    "input": query,
    "chat_history": chat_history
})
```

### Riepilogo: Checklist Implementazione

- [ ] **Vector Store pronto** con documenti caricati e splittati
- [ ] **LLM configurato** (con temperatura bassa ~0.1)
- [ ] **Retriever creato** dal vector store
- [ ] **History Aware Retriever** configurato con:
  - [ ] Prompt di contestualizzazione chiaro
  - [ ] Template con MessagesPlaceholder per chat_history
  - [ ] LLM + retriever + prompt combinati
- [ ] **Question Answer Chain** configurata con:
  - [ ] Prompt che considera context + history
  - [ ] Template con slots per context, chat_history, input
  - [ ] LLM collegato
- [ ] **RAG Chain finale** che combina retrieval + Q&A
- [ ] **Loop conversazionale** implementato con:
  - [ ] Inizializzazione chat_history = []
  - [ ] Aggiornamento storia dopo ogni scambio
  - [ ] Gestione limitazione lunghezza
- [ ] **Testing** con domande contestuali
- [ ] **Logging** e tracking delle fonti

## Best Practices

### 1. Ottimizzazione del Chunking

```python
# Per documenti lunghi
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""]  # Priorità di split
)
```

### 2. Configurazione del Retriever

```python
# Recupera più documenti per contesto migliore
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}  # Top 4 documenti
)
```

### 3. Prompt Engineering

Elementi chiave di un buon prompt RAG:
- Istruzioni chiare sul comportamento
- Gestione esplicita di "non so"
- Vincoli sulla lunghezza della risposta
- Lingua di output specificata

```python
qa_system_prompt = """You are an assistant for question-answering tasks.

INSTRUCTIONS:
- Use ONLY the retrieved context to answer
- If the answer is not in the context, say "Non ho trovato informazioni su questo"
- Keep answers concise (max 3 sentences)
- Reply in Italian
- Cite sources when possible

CONTEXT:
{context}"""
```

### 4. Gestione della Memoria

```python
# Limita la cronologia per evitare token excess
MAX_HISTORY = 10

if len(chat_history) > MAX_HISTORY:
    chat_history = chat_history[-MAX_HISTORY:]
```

### 5. Persistenza del Vector Store

```python
# Salva il vector store su disco
vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=OpenAIEmbeddings(),
    persist_directory="./chroma_db"  # Directory persistente
)

# Carica un vector store esistente
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=OpenAIEmbeddings()
)
```

## Troubleshooting

### Problema: Risposte non rilevanti

**Cause possibili:**
- Chunk size troppo grande/piccolo
- Pochi documenti recuperati
- Embeddings non adeguati

**Soluzioni:**
```python
# Aumenta documenti recuperati
retriever = vectorstore.as_retriever(search_kwargs={"k": 6})

# Ottimizza chunk size
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,  # Prova diverse dimensioni
    chunk_overlap=150
)
```

### Problema: Contesto conversazionale non funziona

**Causa:** Il history aware retriever non riformula correttamente

**Soluzione:** Migliora il prompt di contestualizzazione
```python
contextualization_prompt = """Dato lo storico della conversazione e l'ultima domanda,
riformula la domanda in modo che sia comprensibile senza lo storico.

IMPORTANTE:
- Se la domanda usa pronomi (lui, quello, essa), sostituiscili con i nomi
- Se fa riferimento a messaggi precedenti, includi quel contesto
- Se è già standalone, restituiscila invariata

NON rispondere alla domanda, solo riformulala."""
```

### Problema: Troppi token / Costo elevato

**Soluzioni:**
1. Riduci documenti recuperati
2. Usa un modello più economico per la riformulazione
3. Limita la cronologia conversazionale

```python
# Usa modello economico per riformulazione
cheap_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
history_aware_retriever = create_history_aware_retriever(
    cheap_llm,  # Invece di llm principale
    retriever,
    contextualize_query_prompt
)

# Usa modello potente solo per risposta finale
question_answer_chain = create_stuff_documents_chain(
    expensive_llm,  # GPT-4
    qa_prompt
)
```

### Problema: Vector store lento

**Soluzioni:**
1. Usa un database vettoriale più performante (Pinecone, Weaviate)
2. Implementa caching
3. Riduci dimensione embeddings

```python
# Esempio con cache
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache

set_llm_cache(InMemoryCache())
```

## Architettura Finale

```
User Query
    ↓
History Aware Retriever
    ↓
[Riformula con chat_history] → LLM (cheap)
    ↓
Standalone Query
    ↓
Vector Store Search
    ↓
Retrieved Documents (k=4)
    ↓
Question Answer Chain
    ↓
[Context + Query + History] → LLM (expensive)
    ↓
Final Answer + Sources
```

## Metriche di Valutazione

Per valutare la qualità del sistema RAG:

```python
# 1. Retrieval Quality
def evaluate_retrieval(query, expected_doc_ids):
    results = retriever.get_relevant_documents(query)
    retrieved_ids = [doc.metadata.get('id') for doc in results]
    return len(set(retrieved_ids) & set(expected_doc_ids)) / len(expected_doc_ids)

# 2. Answer Quality
def evaluate_answer(query, expected_answer, chat_history=[]):
    response = rag_chain.invoke({"input": query, "chat_history": chat_history})
    # Usa LLM per valutare similarità
    return response["answer"]
```

## Conclusioni

Questa implementazione fornisce:
- Sistema RAG base per query singole
- History-aware RAG per conversazioni multi-turno
- Gestione automatica del contesto
- Tracciabilità delle fonti

**Prossimi step:**
- Implementare feedback loop per migliorare retrieval
- Aggiungere re-ranking dei documenti
- Implementare streaming per risposte in tempo reale
- Aggiungere valutazione automatica della qualità
