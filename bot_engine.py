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
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool
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
from src.rag.retriever import Retriever

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
        # COMPONENTE 4: Memory Management
        # ========================================
        # Dizionario: user_id → ConversationBufferMemory
        # Ogni utente ha la sua memoria separata!
        logger.info("[4/5] Initializing Memory...")
        self.user_memories: Dict[int, ConversationBufferMemory] = {}
        logger.info("      Per-user memory enabled")

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
        # TOOL 1: RAG Document Search
        # ========================================
        if feature_flags.ENABLE_RAG:
            # IMPORTANTE: Description chiara per l'agent!
            # L'agent decide quando usare il tool basandosi su questa description
            rag_tool = Tool(
                name="ricerca_documenti",
                description=(
                    "Cerca informazioni nei documenti caricati nel database. "
                    "Usa questo tool quando l'utente chiede info su materiale "
                    "specifico caricato (dispense, PDF, documenti). "
                    "Input: domanda dell'utente. "
                    "Output: testo rilevante dai documenti con citazioni."
                ),
                func=self._search_documents
            )
            tools.append(rag_tool)
            logger.info("      [TOOL] RAG Document Search added")

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

            # Wrapper con nome italiano
            web_search_tool = Tool(
                name="ricerca_web",
                description=(
                    "Cerca informazioni su internet. "
                    "Usa questo tool quando l'utente chiede info recenti, "
                    "notizie, o contenuti non presenti nei documenti caricati. "
                    "Input: query di ricerca. "
                    "Output: risultati web aggiornati."
                ),
                func=tavily_tool.run
            )
            tools.append(web_search_tool)
            logger.info("      [TOOL] Web Search added")

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

            # Prepend system prompt al template esistente
            enhanced_template = prompts.SYSTEM_PROMPT + "\n\n" + original_template
            react_prompt.template = enhanced_template

            logger.info("      [OK] Injected custom SYSTEM_PROMPT into agent")

        except Exception as e:
            logger.error(f"      [ERROR] Failed to load prompt from hub: {e}")
            # Fallback: usa prompt basico
            from langchain.prompts import PromptTemplate
            react_prompt = PromptTemplate(
                input_variables=["chat_history", "input", "agent_scratchpad"],
                template=prompts.SYSTEM_PROMPT + "\n\n{input}\n\n{agent_scratchpad}"
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
            handle_parsing_errors=True  # Gestisci errori di parsing gracefully
        )

        logger.info(f"      [OK] Agent executor ready")
        logger.info(f"           Max iterations: {agent_config.MAX_ITERATIONS}")
        logger.info(f"           Verbose: {agent_config.VERBOSE}")

        return agent_executor

    def _get_or_create_memory(self, user_id: int) -> ConversationBufferMemory:
        """
        Ottieni o crea memoria per user_id.

        STUDENTI: Ogni utente ha memoria separata!
        Questo permette conversazioni contestuali per utente.

        Args:
            user_id: Telegram user ID

        Returns:
            ConversationBufferMemory per l'utente

        ESERCIZIO LIVELLO 2:
        Sperimenta con diversi tipi di memory:
        - ConversationSummaryMemory: riassume conversazioni lunghe
        - ConversationBufferWindowMemory: mantiene ultimi N messaggi
        - ConversationKGMemory: estrae knowledge graph
        """
        if user_id not in self.user_memories:
            logger.debug(f"[MEMORY] Creating new memory for user {user_id}")
            self.user_memories[user_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="output"
            )

        return self.user_memories[user_id]

    def _search_documents(self, query: str) -> str:
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
            sources = self.retriever.format_sources(results)

            # ========================================
            # STEP 3: GENERATION
            # ========================================
            # Costruisci prompt con contesto documenti
            augmented_prompt = prompts.RAG_QUERY_PROMPT.format(
                context=context,
                query=query
            )

            # Genera risposta
            response = self.llm.predict(augmented_prompt)

            # Aggiungi citazioni
            final_response = response + "\n\n" + sources

            logger.debug(f"[RAG TOOL] Generated response ({len(final_response)} chars)")
            return final_response

        except Exception as e:
            logger.error(f"[RAG TOOL ERROR] {e}")
            return f"Errore durante ricerca documenti: {str(e)}"

    def process_message(
        self,
        user_message: str,
        user_id: int
    ) -> str:
        """
        Processing principale: messaggio utente → risposta bot.

        Questo è l'entry point principale! Tutto passa da qui.

        Flow:
        1. Recupera memoria utente
        2. Agent decide autonomamente quale tool usare (o nessuno)
        3. Agent esegue tool se necessario
        4. Agent genera risposta finale
        5. Aggiorna memoria

        Args:
            user_message: Messaggio dell'utente
            user_id: Telegram user ID

        Returns:
            Risposta del bot

        Example:
            >>> response = engine.process_message(
            ...     user_message="Cosa dice il documento su Python?",
            ...     user_id=123
            ... )
        """
        logger.info(f"[PROCESS] User {user_id}: '{user_message[:50]}...'")

        try:
            # Ottieni memoria utente
            memory = self._get_or_create_memory(user_id)

            # ========================================
            # Agent Execution
            # ========================================
            # L'agent decide autonomamente:
            # - Usare RAG tool? (se query su documenti)
            # - Usare Web search? (se serve info recenti)
            # - Rispondere direttamente? (se ha già la risposta)
            result = self.agent_executor.invoke({
                "input": user_message,
                "chat_history": memory.buffer_as_messages if hasattr(memory, 'buffer_as_messages') else []
            })

            response = result.get("output", "Mi dispiace, non ho potuto generare una risposta.")

            # Aggiorna memoria
            memory.save_context(
                {"input": user_message},
                {"output": response}
            )

            logger.info(f"[SUCCESS] Generated response ({len(response)} chars)")
            return response

        except Exception as e:
            logger.error(f"[ERROR] Processing failed: {e}")
            import traceback
            traceback.print_exc()
            return f"Mi dispiace, si è verificato un errore: {str(e)[:200]}"

    def clear_memory(self, user_id: int):
        """
        Cancella memoria conversazione per user_id.

        Args:
            user_id: Telegram user ID
        """
        if user_id in self.user_memories:
            del self.user_memories[user_id]
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
