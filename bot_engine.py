"""
LangChain Core Engine

Orchestrates:
- LangChain Agent (ReAct pattern)
- RAG (Retrieval-Augmented Generation)
- Tool calling (RAG + Web Search)
- Memory management per user_id
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
    Motore LangChain per bot con RAG.

    Componenti:
    - LLM (ChatOpenAI)
    - Tools (RAG + Web Search)
    - Agent (ReAct pattern)
    - Memory (per user_id)
    """

    def __init__(self, vector_store):
        """Inizializza LangChain Engine."""
        logger.info("="*60)
        logger.info("[INIT] LangChain Engine")
        logger.info("="*60)

        self.vector_store = vector_store

        logger.info("[1/5] LLM...")
        self.llm = ChatOpenAI(
            model=llm_config.MODEL,
            temperature=llm_config.TEMPERATURE,
            openai_api_key=api_keys.OPENAI_API_KEY,
            max_tokens=llm_config.MAX_TOKENS
        )
        logger.info(f"      {llm_config.MODEL}, temp={llm_config.TEMPERATURE}")

        logger.info("[2/5] Embeddings...")
        self.embeddings = OpenAIEmbeddings(
            model=rag_config.EMBEDDING_MODEL,
            openai_api_key=api_keys.OPENAI_API_KEY
        )
        logger.info(f"      {rag_config.EMBEDDING_MODEL}")

        logger.info("[3/5] Retriever...")
        self.retriever = Retriever(vector_store)
        logger.info(f"      Top-K: {rag_config.TOP_K}")

        logger.info("[4/5] Memory Manager...")
        self.memory_manager = IntelligentMemoryManager()
        logger.info(f"      Max users: {self.memory_manager.max_cached_users}, Token limit: {self.memory_manager.token_limit}")

        logger.info("[5/5] Tools + Agent...")
        self.tools = self._setup_tools()
        self.agent_executor = self._setup_agent()

        logger.info("="*60)
        logger.info(f"[SUCCESS] Engine ready! Tools: {len(self.tools)}, RAG={feature_flags.ENABLE_RAG}, Web={feature_flags.ENABLE_WEB_SEARCH}")
        logger.info("="*60)

    def _setup_tools(self) -> List[Tool]:
        """Setup tools per l'agent."""
        tools = []

        # RAG Document Search
        if feature_flags.ENABLE_RAG:
            doc_list = self._get_document_list_summary()

            rag_tool = StructuredTool.from_function(
                name="ricerca_documenti",
                description=(
                    f"Cerca informazioni nei documenti caricati. "
                    f"Documenti: {doc_list}. "
                    f"Usa per domande su Develhope, Data & AI Week, Vincenzo Orrei. "
                ),
                func=self._search_documents,
                coroutine=self._search_documents
            )
            tools.append(rag_tool)
            logger.info(f"      [TOOL] RAG ({len(self.vector_store.list_all_documents())} docs)")

        # Web Search
        if feature_flags.ENABLE_WEB_SEARCH and api_keys.TAVILY_API_KEY:
            tavily_tool = TavilySearchResults(
                max_results=3,
                search_depth="basic",
                include_answer=True,
                include_raw_content=False,
                api_key=api_keys.TAVILY_API_KEY
            )

            web_search_tool = Tool(
                name="ricerca_web",
                description="Cerca informazioni aggiornate su internet. Usa per notizie recenti.",
                func=tavily_tool.run
            )
            tools.append(web_search_tool)
            logger.info("      [TOOL] Web Search")

        if not tools:
            logger.warning("[WARN] No tools configured!")

        return tools

    def _build_temporal_context(self) -> str:
        """Costruisce sezione temporal info per system prompt."""
        now = datetime.now()
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

        return f"\n📅 Data: {giorni[now.weekday()]} {now.day} {mesi[now.month - 1]} {now.year}, Ora: {now.hour:02d}:{now.minute:02d}\n"

    def _get_document_list_summary(self) -> str:
        """Lista documenti compatta per tool description."""
        try:
            documents = self.vector_store.list_all_documents()
            if not documents:
                return "Nessun documento"

            names = [doc.get('source', 'Unknown') for doc in documents[:5]]
            doc_list = ", ".join(names)
            if len(documents) > 5:
                doc_list += f" (+ {len(documents) - 5})"
            return doc_list

        except Exception as e:
            logger.error(f"[ERROR] Document list: {e}")
            return "Errore"

    def _build_documents_context(self) -> str:
        """Costruisce sezione documenti per system prompt."""
        try:
            documents = self.vector_store.list_all_documents()

            if not documents:
                return "\nNESSUN DOCUMENTO CARICATO.\n"

            context = "\n" + "="*60 + "\n"
            context += "DOCUMENTI DISPONIBILI:\n"
            context += "="*60 + "\n"

            for doc in documents:
                source = doc.get('source', 'Unknown')
                summary = doc.get('summary', 'No summary')
                context += f"📄 {source}: {summary}\n"

            context += "="*60 + "\n"
            context += "Usa 'ricerca_documenti' per domande su questi documenti.\n"
            context += "="*60 + "\n"

            return context

        except Exception as e:
            logger.error(f"[ERROR] Documents context: {e}")
            return "\n⚠️  Errore documenti.\n"

    def _custom_parsing_error_handler(self, error: Exception) -> str:
        """Handler per parsing errors dell'agent."""
        logger.warning(f"⚠️  Agent parsing error: {error}")
        return "Invalid Format: Agent parsing error - fallback required"

    def _setup_agent(self) -> AgentExecutor:
        """Setup agent con ReAct pattern."""
        logger.info("      Setting up ReAct agent...")

        try:
            react_prompt = hub.pull("hwchase17/react-chat")
            logger.info("      [OK] Loaded react-chat prompt")

            # Inject custom system prompt
            temporal_context = self._build_temporal_context()
            documents_context = self._build_documents_context()
            full_system_prompt = prompts.SYSTEM_PROMPT + temporal_context + documents_context

            react_prompt.template = full_system_prompt + "\n\n" + react_prompt.template
            logger.info("      [OK] Injected custom system prompt")

        except Exception as e:
            logger.error(f"      [ERROR] Prompt loading failed: {e}")
            from langchain.prompts import PromptTemplate
            temporal_context = self._build_temporal_context()
            documents_context = self._build_documents_context()
            full_system_prompt = prompts.SYSTEM_PROMPT + temporal_context + documents_context
            react_prompt = PromptTemplate(
                input_variables=["chat_history", "input", "agent_scratchpad"],
                template=full_system_prompt + "\n\n{input}\n\n{agent_scratchpad}"
            )

        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=react_prompt
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=agent_config.VERBOSE,
            max_iterations=agent_config.MAX_ITERATIONS,
            early_stopping_method=agent_config.EARLY_STOPPING_METHOD,
            handle_parsing_errors=self._custom_parsing_error_handler
        )

        logger.info(f"      [OK] Agent ready (max_iter={agent_config.MAX_ITERATIONS}, verbose={agent_config.VERBOSE})")

        return agent_executor

    def _get_or_create_memory(self, user_id: int):
        """Ottieni o crea memoria per user_id."""
        return self.memory_manager.get_memory(user_id)

    async def _search_documents(self, query: str) -> str:
        """
        Tool function: Simple RAG search.

        Agent handles context via chat_history, this tool just retrieves documents.

        Args:
            query: Query dell'utente

        Returns:
            Risposta dai documenti
        """
        logger.debug(f"[RAG TOOL] '{query[:50]}...'")

        try:
            results = self.retriever.retrieve(query=query, k=rag_config.TOP_K)

            if not results:
                return prompts.RAG_NO_CONTEXT_PROMPT

            context = self.retriever.format_context(results)

            augmented_prompt = prompts.RAG_QUERY_PROMPT.format(
                context=context,
                query=query
            )

            from langchain_core.messages import HumanMessage
            response_message = await self.llm.ainvoke([HumanMessage(content=augmented_prompt)])

            return response_message.content

        except Exception as e:
            logger.error(f"[RAG TOOL ERROR] {e}")
            return f"Errore: {str(e)}"

    async def process_message(
        self,
        user_message: str,
        user_id: int
    ) -> str:
        """
        Processing principale: Agent decide quando usare RAG history-aware.

        Flow semplificato:
        1. Recupera memoria utente
        2. Agent orchestra tools (include RAG history-aware come tool)
        3. Salva interazione in memoria

        Args:
            user_message: Messaggio dell'utente
            user_id: Telegram user ID

        Returns:
            Risposta del bot
        """
        logger.info(f"[PROCESS] User {user_id}: '{user_message[:50]}...'")

        try:
            # Get user memory
            memory = self._get_or_create_memory(user_id)

            # Load chat history from memory
            memory_variables = memory.load_memory_variables({})
            chat_history = memory_variables.get("chat_history", [])

            logger.info(f"[MEMORY] {len(chat_history)} messages")

            # Agent orchestration
            result = await self.agent_executor.ainvoke({
                "input": user_message,
                "chat_history": chat_history
            })

            response = result.get("output", "Mi dispiace, non ho potuto generare una risposta.")

            # Save interaction
            self.memory_manager.save_interaction(user_id, user_message, response)

            logger.info(f"[SUCCESS] {len(response)} chars")
            return response

        except Exception as e:
            logger.error(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
            return f"Mi dispiace, si è verificato un errore: {str(e)[:200]}"

    def refresh_agent(self):
        """
        Ricrea tools e agent con contesto documenti aggiornato.

        Chiamare dopo upload/eliminazione documenti.
        """
        logger.info("[REFRESH] Rebuilding agent...")

        try:
            self.tools = self._setup_tools()
            self.agent_executor = self._setup_agent()

            logger.info("[REFRESH] Complete!")
            logger.info(f"[REFRESH] Tools: {len(self.tools)}, Docs: {len(self.vector_store.list_all_documents())}")

        except Exception as e:
            logger.error(f"[REFRESH] Failed: {e}")
            import traceback
            traceback.print_exc()

    def clear_memory(self, user_id: int):
        """Cancella memoria conversazione per user_id."""
        self.memory_manager.clear_memory(user_id)
        logger.info(f"[MEMORY] Cleared for user {user_id}")


if __name__ == "__main__":
    print("LangChain Core Engine")
    print("Requires: Vector store + API keys")
    print("Run: python main.py")
