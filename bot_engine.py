"""
LangChain Core Engine - CUORE DIDATTICO DEL BOT

Questo è il file PIÙ IMPORTANTE del progetto!
Gli studenti impareranno qui i concetti fondamentali di:
- LangChain Agents (ReAct pattern)
- RAG (Retrieval-Augmented Generation)
- Tool calling
- Memory management
- Agent orchestration

ATTENZIONI CRITICHE per STUDENTI:
❌ `initialize_agent` è DEPRECATO in LangChain 0.3.x
✅ Usare `create_react_agent` + `AgentExecutor`
✅ Memory separata per user_id
✅ Tools: RAG + Web Search + Direct Answer

ESERCIZI PROGRESSIVI (alla fine del file):
- Livello 1: Modifica temperature, top_k
- Livello 2: Personalizza prompts
- Livello 3: Aggiungi nuovo tool
- Livello 4: Implementa feedback loop
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool, StructuredTool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain import hub

from config import (
    api_keys,
    llm_config,
    rag_config,
    agent_config,
    feature_flags
)
from prompts import prompts
from src.utils.logger import get_logger
from src.utils.helpers import convert_markdown_to_html
from src.rag.retriever import Retriever
from src.utils.intelligent_memory_manager import IntelligentMemoryManager

logger = get_logger(__name__)


class LangChainEngine:
    """
    Motore LangChain per bot educativo con RAG.

    Questo engine orchestrata:
    1. **LLM**: ChatOpenAI per generazione risposte
    2. **Tools**: RAG retriever + Tavily web search
    3. **Agent**: ReAct pattern per reasoning + action
    4. **Memory**: Conversazione per ogni user_id

    Architecture Flow:
    User Query → Agent Reasoning → Tool Selection → Tool Execution → Response

    Example:
        >>> engine = LangChainEngine(vector_store)
        >>> response = engine.process_message(
        ...     user_message="What is AI?",
        ...     user_id=123
        ... )
        >>> print(response)
    """

    def __init__(self, vector_store):
        """
        Inizializza LangChain Engine.

        STUDENTI: Studiate attentamente questo __init__!
        Ogni componente ha un ruolo specifico nell'architettura.

        Args:
            vector_store: VectorStoreManager instance per RAG
        """
        logger.info("="*60)
        logger.info("[INIT] LangChain Engine - CORE DIDATTICO")
        logger.info("="*60)

        self.vector_store = vector_store

        # ========================================
        # COMPONENTE 1: LLM (Large Language Model)
        # ========================================
        # ChatOpenAI è il modello che genera le risposte
        # Temperature: 0.0 = deterministico, 1.0 = creativo
        logger.info("[1/5] Initializing LLM...")
        self.llm = ChatOpenAI(
            model=llm_config.MODEL,
            temperature=llm_config.TEMPERATURE,
            openai_api_key=api_keys.OPENAI_API_KEY,
            max_tokens=llm_config.MAX_TOKENS
        )
        logger.info(f"      Model: {llm_config.MODEL}")
        logger.info(f"      Temperature: {llm_config.TEMPERATURE}")

        # ========================================
        # COMPONENTE 2: Embeddings (per RAG)
        # ========================================
        # Gli embeddings trasformano testo in vettori numerici
        # Usati per similarity search nel vector store
        logger.info("[2/5] Initializing Embeddings...")
        self.embeddings = OpenAIEmbeddings(
            model=rag_config.EMBEDDING_MODEL,
            openai_api_key=api_keys.OPENAI_API_KEY
        )
        logger.info(f"      Model: {rag_config.EMBEDDING_MODEL}")

        # ========================================
        # COMPONENTE 3: Retriever (RAG)
        # ========================================
        # Il retriever cerca documenti rilevanti nel vector store
        logger.info("[3/5] Initializing Retriever...")
        self.retriever = Retriever(vector_store)
        logger.info(f"      Top-K: {rag_config.TOP_K}")

        # ========================================
        # COMPONENTE 4: Intelligent Memory Management
        # ========================================
        # IntelligentMemoryManager con:
        # - Auto-summarization (ConversationSummaryBufferMemory)
        # - LRU eviction (max 100 users in RAM)
        # - Disk persistence (JSON)
        # - Auto-cleanup conversazioni vecchie
        logger.info("[4/5] Initializing Intelligent Memory Manager...")
        self.memory_manager = IntelligentMemoryManager()
        logger.info("      Hybrid memory: Summary + Recent buffer")
        logger.info(f"      Max cached users: {self.memory_manager.max_cached_users}")
        logger.info(f"      Token limit: {self.memory_manager.token_limit}")

        # ========================================
        # COMPONENTE 5: Tools + Agent
        # ========================================
        logger.info("[5/5] Setting up Tools and Agent...")
        self.tools = self._setup_tools()
        self.agent_executor = self._setup_agent()

        logger.info("="*60)
        logger.info("[SUCCESS] LangChain Engine ready!")
        logger.info(f"          Tools: {len(self.tools)}")
        logger.info(f"          Features: RAG={feature_flags.ENABLE_RAG}, "
                   f"Web={feature_flags.ENABLE_WEB_SEARCH}")
        logger.info("="*60)

    def _setup_tools(self) -> List[Tool]:
        """
        Setup tools disponibili per l'agent.

        Tools = "funzioni" che l'agent può chiamare per ottenere info.

        STUDENTI: Questo è dove aggiungere nuovi tools!
        Ogni tool ha:
        - name: identificativo univoco
        - description: spiega all'agent quando usarlo
        - func: funzione Python da eseguire

        Returns:
            Lista di Tool objects

        ESERCIZIO LIVELLO 3:
        Aggiungi un nuovo tool! Ad esempio:
        - Calculator: per fare calcoli matematici
        - Wikipedia: per info enciclopediche
        - Weather: per meteo
        """
        tools = []

        # ========================================
        # TOOL 1: RAG Document Search (ASYNC)
        # ========================================
        if feature_flags.ENABLE_RAG:
            # IMPORTANTE: Description chiara per l'agent!
            # L'agent decide quando usare il tool basandosi su questa description
            # Usa StructuredTool per supportare async coroutines

            # Ottieni lista documenti disponibili per description
            doc_list = self._get_document_list_summary()

            # Description POTENZIATA con esempi e documenti disponibili
            rag_tool = StructuredTool.from_function(
                name="ricerca_documenti",
                description=(
                    "🔍 **RICERCA NEI DOCUMENTI CARICATI DAGLI ADMIN** 🔍\n\n"

                    "📂 DOCUMENTI ATTUALMENTE DISPONIBILI:\n"
                    f"{doc_list}\n\n"

                    "✅ QUANDO USARE QUESTO TOOL (esempi):\n"
                    "- Domande su persone/organizzazioni menzionate nei documenti\n"
                    "  Esempi: 'Chi è Vincenzo Orrei?', 'Cosa fa Develhope?'\n"
                    "- Domande su contenuti specifici di corsi/guide/materiali\n"
                    "  Esempi: 'Che corsi offre?', 'Quali sono i prerequisiti?'\n"
                    "- Richieste di informazioni presenti nei documenti caricati\n"
                    "  Esempi: 'Parlami del curriculum', 'Spiega il programma'\n"
                    "- Qualsiasi domanda che sembra correlata ai nomi file sopra\n\n"

                    "⚠️ IMPORTANTE:\n"
                    "- SEMPRE preferibile a ricerca_web se la risposta potrebbe essere nei documenti!\n"
                    "- Cerca PRIMA qui, poi usa web search solo se non trovi nulla\n"
                    "- I documenti contengono informazioni specifiche e affidabili\n\n"

                    "📥 Input: domanda dell'utente (stringa)\n"
                    "📤 Output: risposta basata sui documenti con citazioni delle fonti"
                ),
                func=self._search_documents,
                coroutine=self._search_documents  # Async support
            )
            tools.append(rag_tool)
            logger.info(f"      [TOOL] RAG Document Search added (async) - {len(self.vector_store.list_all_documents())} docs available")

        # ========================================
        # TOOL 2: Web Search (Tavily)
        # ========================================
        if feature_flags.ENABLE_WEB_SEARCH and api_keys.TAVILY_API_KEY:
            tavily_tool = TavilySearchResults(
                max_results=3,
                search_depth="basic",  # "basic" or "advanced"
                include_answer=True,
                include_raw_content=False,
                api_key=api_keys.TAVILY_API_KEY
            )

            # Wrapper con nome italiano e description migliorata
            web_search_tool = Tool(
                name="ricerca_web",
                description=(
                    "🌐 **RICERCA SU INTERNET (Tavily Web Search)** 🌐\n\n"

                    "✅ QUANDO USARE QUESTO TOOL:\n"
                    "- Informazioni recenti o notizie correnti\n"
                    "  Esempi: 'Ultime notizie su AI', 'Eventi tech oggi'\n"
                    "- Contenuti NON presenti nei documenti caricati\n"
                    "- Dopo aver provato ricerca_documenti senza successo\n"
                    "- Domande su eventi, persone, aziende NON menzionate nei documenti\n\n"

                    "⚠️ IMPORTANTE:\n"
                    "- Usa SOLO se ricerca_documenti non ha dato risultati\n"
                    "- NON usare per domande che potrebbero essere nei documenti!\n"
                    "- Preferisci sempre i documenti caricati (più affidabili)\n\n"

                    "📥 Input: query di ricerca (stringa)\n"
                    "📤 Output: risultati web aggiornati con fonti"
                ),
                func=tavily_tool.run
            )
            tools.append(web_search_tool)
            logger.info("      [TOOL] Web Search added (fallback option)")

        # ========================================
        # ESERCIZIO: Aggiungi i tuoi tool qui!
        # ========================================
        # Esempio:
        # calculator_tool = Tool(
        #     name="calculator",
        #     description="Esegue calcoli matematici. Input: espressione matematica.",
        #     func=lambda x: str(eval(x))  # ATTENZIONE: eval() non sicuro in produzione!
        # )
        # tools.append(calculator_tool)

        if not tools:
            logger.warning("[WARN] No tools configured!")

        return tools

    def _build_temporal_context(self) -> str:
        """
        Costruisce sezione INFORMAZIONI TEMPORALI per system prompt.

        Fornisce all'agent awareness della data corrente per:
        - Contestualizzare risposte temporali
        - Migliorare ricerche web su eventi recenti
        - Rispondere a domande tipo "cosa è successo oggi?"

        Returns:
            Stringa formattata con data e giorno correnti

        Example output:
            📅 INFORMAZIONI TEMPORALI
            Data odierna: Sabato 4 Gennaio 2025
        """
        now = datetime.now()

        # Nomi giorni in italiano
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        giorno_settimana = giorni[now.weekday()]

        # Nomi mesi in italiano
        mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        mese = mesi[now.month - 1]

        temporal_context = f"\n📅 INFORMAZIONI TEMPORALI\n"
        temporal_context += f"Data odierna: {giorno_settimana} {now.day} {mese} {now.year}\n"
        temporal_context += f"Ora: {now.hour:02d}:{now.minute:02d}\n"

        return temporal_context

    def _get_document_list_summary(self) -> str:
        """
        Ottiene lista compatta di documenti per tool description.

        Usata nelle description dei tools per dare all'agent visibility
        sui documenti disponibili senza appesantire la description.

        Returns:
            Stringa compatta con nomi documenti (max 5, poi "...")

        Example output:
            "curriculum_tutor.md, develhope.md, python_guide.pdf"
            "doc1.pdf, doc2.pdf, doc3.pdf, doc4.pdf, doc5.pdf (+ 3 altri)"
        """
        try:
            documents = self.vector_store.list_all_documents()

            if not documents:
                return "Nessun documento caricato"

            # Prendi max 5 nomi documenti
            names = [doc.get('source', 'Unknown') for doc in documents[:5]]
            doc_list = ", ".join(names)

            # Se ci sono più di 5, aggiungi indicatore
            if len(documents) > 5:
                doc_list += f" (+ {len(documents) - 5} altri)"

            return doc_list

        except Exception as e:
            logger.error(f"[ERROR] Failed to get document list: {e}")
            return "Errore caricamento lista documenti"

    def _build_documents_context(self) -> str:
        """
        Costruisce sezione DOCUMENTI DISPONIBILI per system prompt.

        Questa sezione fornisce all'agent visibilità sui documenti
        caricati, aiutandolo a decidere quando usare il RAG tool.

        Returns:
            Stringa formattata con lista documenti e sommari

        Example output:
            DOCUMENTI DISPONIBILI NEL DATABASE:
            - doc_abc123: "Guida Python - variabili, loop, funzioni"
            - doc_def456: "Introduzione n8n - workflow automation"
        """
        try:
            # Ottieni lista documenti dal vector store
            documents = self.vector_store.list_all_documents()

            if not documents:
                return "\nNESSUN DOCUMENTO CARICATO: Il database è vuoto.\n"

            # Costruisci sezione formattata
            context = "\n" + "="*60 + "\n"
            context += "DOCUMENTI DISPONIBILI NEL DATABASE:\n"
            context += "="*60 + "\n"

            for doc in documents:
                doc_id = doc.get('doc_id', 'unknown')
                source = doc.get('source', 'Unknown')
                summary = doc.get('summary', 'No summary')
                num_chunks = doc.get('num_chunks', 0)

                context += f"📄 {source} (ID: {doc_id})\n"
                context += f"   Contenuto: {summary}\n"
                context += f"   Chunks: {num_chunks}\n\n"

            context += "="*60 + "\n"
            context += "IMPORTANTE: Usa il tool 'ricerca_documenti' quando l'utente fa domande correlate a questi documenti!\n"
            context += "="*60 + "\n"

            return context

        except Exception as e:
            logger.error(f"[ERROR] Failed to build documents context: {e}")
            return "\n⚠️  Errore recupero documenti disponibili.\n"

    def _custom_parsing_error_handler(self, error: Exception) -> str:
        """
        Custom error handler per parsing errors dell'agent.

        Quando il parser ReAct fallisce (es. formato output non valido),
        restituisce un marker che il sistema di retry può rilevare.

        IMPORTANTE: Restituisce "Invalid Format" così message_processor.py
        può rilevare l'errore e attivare il fallback a RAG diretto.

        Args:
            error: L'eccezione di parsing sollevata

        Returns:
            str: Marker per indicare parsing error
        """
        logger.warning(f"⚠️  Agent parsing error: {error}")
        # CRITICO: Include "Invalid Format" per il sistema di retry in message_processor
        return "Invalid Format: Agent parsing error - fallback required"

    def _setup_agent(self) -> AgentExecutor:
        """
        Setup agent usando ReAct pattern.

        IMPORTANTE per STUDENTI:
        ❌ NON usare `initialize_agent` (deprecato in 0.3.x)
        ✅ Usare `create_react_agent` + `AgentExecutor`

        ReAct = Reasoning + Acting
        L'agent:
        1. Ragiona (Thought)
        2. Decide azione (Action)
        3. Esegue tool (Action Input)
        4. Osserva risultato (Observation)
        5. Ripete fino a risposta finale (Final Answer)

        Returns:
            AgentExecutor configurato
        """
        logger.info("      Setting up ReAct agent...")

        # ========================================
        # Pull ReAct prompt da LangChain Hub
        # ========================================
        # Questo prompt istruisce l'agent su come ragionare
        try:
            react_prompt = hub.pull("hwchase17/react-chat")
            logger.info("      [OK] Loaded react-chat prompt from hub")

            # IMPORTANTE: Inietta il nostro SYSTEM_PROMPT personalizzato
            # Il prompt da hub non sa delle nostre capacità vocali!
            # Modifichiamo il template per includere il system prompt
            original_template = react_prompt.template

            # Costruisci system prompt con contesto temporale e documenti
            temporal_context = self._build_temporal_context()
            documents_context = self._build_documents_context()
            full_system_prompt = prompts.SYSTEM_PROMPT + temporal_context + documents_context

            # Prepend system prompt al template esistente
            enhanced_template = full_system_prompt + "\n\n" + original_template
            react_prompt.template = enhanced_template

            logger.info("      [OK] Injected custom SYSTEM_PROMPT with documents context into agent")

        except Exception as e:
            logger.error(f"      [ERROR] Failed to load prompt from hub: {e}")
            # Fallback: usa prompt basico
            from langchain.prompts import PromptTemplate
            temporal_context = self._build_temporal_context()
            documents_context = self._build_documents_context()
            full_system_prompt = prompts.SYSTEM_PROMPT + temporal_context + documents_context
            react_prompt = PromptTemplate(
                input_variables=["chat_history", "input", "agent_scratchpad"],
                template=full_system_prompt + "\n\n{input}\n\n{agent_scratchpad}"
            )

        # ========================================
        # Create ReAct Agent
        # ========================================
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=react_prompt
        )

        # ========================================
        # Create Agent Executor
        # ========================================
        # L'executor gestisce il loop: thought → action → observation
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=agent_config.VERBOSE,
            max_iterations=agent_config.MAX_ITERATIONS,
            early_stopping_method=agent_config.EARLY_STOPPING_METHOD,
            handle_parsing_errors=self._custom_parsing_error_handler  # Custom handler per errori parsing
        )

        logger.info(f"      [OK] Agent executor ready")
        logger.info(f"           Max iterations: {agent_config.MAX_ITERATIONS}")
        logger.info(f"           Verbose: {agent_config.VERBOSE}")

        return agent_executor

    def _get_or_create_memory(self, user_id: int):
        """
        Ottieni o crea memoria per user_id (usando IntelligentMemoryManager).

        STUDENTI: Ogni utente ha memoria separata!
        Ora con features avanzate:
        - Auto-summarization quando supera token limit
        - LRU eviction per gestione RAM efficiente
        - Persistenza su disco (conversazioni sopravvivono al restart)

        Args:
            user_id: Telegram user ID

        Returns:
            ConversationSummaryBufferMemory per l'utente

        ESERCIZIO LIVELLO 2:
        Verifica il comportamento auto-summarization:
        1. Invia 20+ messaggi lunghi
        2. Usa /memory_stats per vedere token count
        3. Osserva quando triggera summarization (>1500 tokens)
        """
        return self.memory_manager.get_memory(user_id)

    async def _search_documents(self, query: str) -> str:
        """
        Tool function: Cerca documenti nel vector store (RAG).

        Questa funzione viene chiamata dall'agent quando decide
        di usare il tool "ricerca_documenti".

        Pipeline RAG completo:
        1. RETRIEVAL: Similarity search nel vector store
        2. AUGMENTATION: Costruisce prompt con documenti recuperati
        3. GENERATION: LLM genera risposta basata su documenti

        Args:
            query: Query dell'utente

        Returns:
            Risposta generata con citazioni

        ESERCIZIO LIVELLO 4:
        Implementa feedback loop:
        - Se risposta non soddisfacente, ri-retrieva con query riformulata
        - Usa confidence score per decidere se servono più documenti
        """
        logger.debug(f"[RAG TOOL] Searching documents for: '{query[:50]}...'")

        try:
            # ========================================
            # STEP 1: RETRIEVAL
            # ========================================
            results = self.retriever.retrieve(
                query=query,
                k=rag_config.TOP_K
            )

            if not results:
                return prompts.RAG_NO_CONTEXT_PROMPT

            # ========================================
            # STEP 2: AUGMENTATION
            # ========================================
            context = self.retriever.format_context(results)
            # sources = self.retriever.format_sources(results)  # Fonti non più mostrate

            # ========================================
            # STEP 3: GENERATION (ASYNC)
            # ========================================
            # Costruisci prompt con contesto documenti
            augmented_prompt = prompts.RAG_QUERY_PROMPT.format(
                context=context,
                query=query
            )

            # Genera risposta (ASYNC) - usa ainvoke invece di apredict (deprecato)
            from langchain_core.messages import HumanMessage
            response_message = await self.llm.ainvoke([HumanMessage(content=augmented_prompt)])
            response = response_message.content

            # ✅ MANTIENI MARKDOWN PURO per il parser ReAct
            # La conversione HTML avverrà in process_message() dopo che l'agent completa

            # Citazioni fonti rimosse (risposta più pulita)
            final_response = response

            logger.debug(f"[RAG TOOL] Generated response ({len(final_response)} chars)")
            return final_response

        except Exception as e:
            logger.error(f"[RAG TOOL ERROR] {e}")
            return f"Errore durante ricerca documenti: {str(e)}"

    async def process_message(
        self,
        user_message: str,
        user_id: int
    ) -> str:
        """
        Processing principale: messaggio utente → risposta bot (ASYNC).

        Questo è l'entry point principale! Tutto passa da qui.

        Flow:
        1. Recupera memoria utente
        2. **BUILD FRESH DOCUMENT CONTEXT** (CRITICAL FIX!)
        3. Inject context nel prompt per agent awareness
        4. Agent decide autonomamente quale tool usare (o nessuno)
        5. Agent esegue tool se necessario
        6. Agent genera risposta finale
        7. Aggiorna memoria

        IMPORTANTE REFACTOR:
        - Ora usa ainvoke() invece di invoke() per esecuzione asincrona
        - Non blocca l'event loop durante chiamate LLM/API
        - Permette gestione concorrente di multipli utenti
        - **DYNAMIC CONTEXT INJECTION**: Agent vede documenti aggiornati ad ogni query!

        Args:
            user_message: Messaggio dell'utente
            user_id: Telegram user ID

        Returns:
            Risposta del bot

        Example:
            >>> response = await engine.process_message(
            ...     user_message="Cosa dice il documento su Python?",
            ...     user_id=123
            ... )
        """
        logger.info(f"[PROCESS] User {user_id}: '{user_message[:50]}...'")

        try:
            # Ottieni memoria utente
            memory = self._get_or_create_memory(user_id)

            # ========================================
            # DYNAMIC DOCUMENT CONTEXT INJECTION (FIX CRITICO!)
            # ========================================
            # Costruisci contesto documenti FRESCO per OGNI query
            # Questo risolve il problema: agent vede sempre lista aggiornata!
            documents_context = self._build_documents_context()

            # Prepend al messaggio utente per dare context all'agent
            # L'agent vedrà la lista documenti PRIMA di decidere quale tool usare
            enhanced_input = f"{documents_context}\n\n{'='*60}\nDOMANDA UTENTE:\n{'='*60}\n{user_message}"

            logger.debug(f"[CONTEXT] Injected fresh document context ({len(documents_context)} chars)")

            # ========================================
            # Agent Execution (ASYNC)
            # ========================================
            # L'agent decide autonomamente:
            # - Usare RAG tool? (se query su documenti) ← Ora vede i documenti!
            # - Usare Web search? (se serve info recenti)
            # - Rispondere direttamente? (se ha già la risposta)
            result = await self.agent_executor.ainvoke({
                "input": enhanced_input,  # ← USA INPUT ENHANCED con context!
                "chat_history": memory.buffer_as_messages if hasattr(memory, 'buffer_as_messages') else []
            })

            response = result.get("output", "Mi dispiace, non ho potuto generare una risposta.")

            # ✅ NON convertiamo HTML qui - la conversione avviene in message_processor.py
            # Questo evita doppia conversione e mantiene il testo puro per il parser ReAct

            # Salva interazione con IntelligentMemoryManager
            # Salva il messaggio ORIGINALE (non enhanced) per memoria pulita
            self.memory_manager.save_interaction(user_id, user_message, response)

            logger.info(f"[SUCCESS] Generated response ({len(response)} chars)")
            return response

        except Exception as e:
            logger.error(f"[ERROR] Processing failed: {e}")
            import traceback
            traceback.print_exc()
            return f"Mi dispiace, si è verificato un errore: {str(e)[:200]}"

    def refresh_agent(self):
        """
        Ricrea agent con contesto documenti aggiornato.

        QUANDO CHIAMARE:
        - Dopo upload nuovo documento
        - Dopo eliminazione documento
        - Dopo modifica summary documento

        Questo garantisce che:
        1. Tool descriptions includano lista documenti aggiornata
        2. System prompt contenga documenti più recenti
        3. Agent abbia awareness corretta delle risorse disponibili

        Note:
        - Operazione rapida (~100ms)
        - Memoria utenti NON viene cancellata
        - Tools vengono ricreati con descriptions aggiornate
        - Agent executor viene ricreato con nuovo prompt
        """
        logger.info("[REFRESH] Rebuilding agent with updated document context...")

        try:
            # Ricrea tools con descriptions aggiornate
            self.tools = self._setup_tools()

            # Ricrea agent executor con nuovo system prompt
            self.agent_executor = self._setup_agent()

            logger.info("[REFRESH] ✅ Agent refreshed successfully!")
            logger.info(f"[REFRESH]    Tools: {len(self.tools)}")
            logger.info(f"[REFRESH]    Documents available: {len(self.vector_store.list_all_documents())}")

        except Exception as e:
            logger.error(f"[REFRESH] ❌ Failed to refresh agent: {e}")
            import traceback
            traceback.print_exc()

    def clear_memory(self, user_id: int):
        """
        Cancella memoria conversazione per user_id.

        Usa IntelligentMemoryManager che gestisce:
        - Rimozione da RAM
        - Eliminazione file da disco
        - Reset counters

        Args:
            user_id: Telegram user ID
        """
        self.memory_manager.clear_memory(user_id)
        logger.info(f"[MEMORY] Cleared for user {user_id}")


# ========================================
# ESERCIZI PROGRESSIVI per STUDENTI
# ========================================
"""
🎓 ESERCIZIO LIVELLO 1: Sperimentare con Parametri
-------------------------------------------------
Modifica questi parametri in config.py e osserva i cambiamenti:

1. LLM Temperature (0.0 - 1.0):
   - 0.0: Risposte deterministiche, precise
   - 0.7: Bilanciato (default)
   - 1.0: Risposte creative, variabili

2. RAG Top-K (1-10):
   - 1-3: Veloce, meno contesto
   - 3-5: Bilanciato (default)
   - 5-10: Più contesto, più lento

3. Chunk Size (300-2000):
   - Piccolo: Più preciso, meno contesto
   - Grande: Più contesto, meno preciso

Domanda: Come cambia la qualità delle risposte?


🎓 ESERCIZIO LIVELLO 2: Personalizzare Prompts
----------------------------------------------
Modifica i prompts in prompts.py:

1. SYSTEM_PROMPT:
   - Cambia tono (formale/informale)
   - Aggiungi istruzioni specifiche
   - Definisci area expertise

2. RAG_QUERY_PROMPT:
   - Cambia stile citazioni
   - Aggiungi constraints
   - Modifica output format

Domanda: Come influenzano le risposte?


🎓 ESERCIZIO LIVELLO 3: Aggiungere Nuovo Tool
---------------------------------------------
Nel metodo _setup_tools(), aggiungi:

1. Calculator Tool:
   ```python
   from langchain.tools import Tool

   def calculate(expression: str) -> str:
       try:
           # ATTENZIONE: eval() non è sicuro in produzione!
           # Usa librerie come numexpr per sicurezza
           result = eval(expression)
           return f"Risultato: {result}"
       except Exception as e:
           return f"Errore calcolo: {e}"

   calculator_tool = Tool(
       name="calcolatrice",
       description="Esegue calcoli matematici. Input: espressione (es: '2+2', '10*5').",
       func=calculate
   )
   tools.append(calculator_tool)
   ```

2. Weather Tool:
   - Integra API meteo (es: OpenWeatherMap)
   - Description chiara per agent
   - Gestione errori robusta

Domanda: L'agent usa il tool correttamente?


🎓 ESERCIZIO LIVELLO 4: Implementare Feedback Loop
--------------------------------------------------
Migliora il metodo _search_documents():

1. Valuta qualità risposta:
   - Usa similarity score
   - Check se risposta è rilevante
   - Conta documenti utilizzati

2. Se qualità bassa, ri-retrieva:
   - Riformula query
   - Aumenta Top-K
   - Prova diversi filtri

3. Implementa max_retries:
   - Evita loop infiniti
   - Log tentativi
   - Fallback a web search

Pseudocodice:
```python
max_retries = 3
for attempt in range(max_retries):
    results = retriever.retrieve(query, k=top_k)

    if quality_check(results):
        break

    # Increase top_k for next attempt
    top_k += 2

    # Rephrase query
    query = rephrase_query(query)
```


🎓 ESERCIZIO AVANZATO: Custom Agent Type
----------------------------------------
Oltre a ReAct, LangChain supporta altri agent types:

1. Conversational ReAct:
   - Migliore per chat multi-turn
   - Usa memoria più efficacemente

2. Structured Chat:
   - Per tool con input complessi
   - Schema validation

3. OpenAI Functions:
   - Usa native function calling
   - Più affidabile per tool selection

Prova a sostituire create_react_agent con altri tipi!


📚 RISORSE APPROFONDIMENTO:
--------------------------
- LangChain Docs: https://python.langchain.com/docs/
- ReAct Paper: https://arxiv.org/abs/2210.03629
- RAG Tutorial: https://python.langchain.com/docs/tutorials/rag/
- Agent Types: https://python.langchain.com/docs/modules/agents/agent_types/
"""


if __name__ == "__main__":
    print("LangChain Core Engine - Cuore Didattico")
    print("\nQSuesto modulo richiede:")
    print("  - Vector store inizializzato")
    print("  - API keys configurate")
    print("\nEsegui il bot completo con: python main.py")
