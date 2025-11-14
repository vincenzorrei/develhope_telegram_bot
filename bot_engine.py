"""
LangChain Core Engine

Orchestrates:
- LLM with function calling (native tool binding)
- RAG (Retrieval-Augmented Generation) with history-aware retriever
- Tool calling (RAG + Web Search)
- Memory management per user_id with summary buffer
  - Session store: in-memory chat history per user
  - Summary buffer: automatic summarization when conversation gets long
  - History-aware retrieval: contextualizes queries based on chat history
"""

from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from config import (
    api_keys,
    llm_config,
    rag_config,
    agent_config,
    memory_config,
    feature_flags
)
from prompts import prompts
from src.utils.logger import get_logger
from src.utils.helpers import convert_markdown_to_html
from src.rag.retriever import Retriever

logger = get_logger(__name__)


class LangChainEngine:
    """
    Motore LangChain per bot con RAG.

    Componenti:
    - LLM (ChatOpenAI) with native function calling
    - Tools (RAG + Web Search)
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

        logger.info("[3/5] Retriever + History-Aware...")
        self.retriever = Retriever(vector_store)
        self.history_aware_retriever = self._setup_history_aware_retriever()
        logger.info(f"      Top-K: {rag_config.TOP_K}, History-aware: enabled")

        logger.info("[4/5] Session Store...")
        self.session_store: Dict[int, ChatMessageHistory] = {}
        logger.info(f"      Summary buffer threshold: {memory_config.MAX_TOKENS_BEFORE_SUMMARY} tokens")

        logger.info("[5/5] Tools + LLM binding...")
        self.tools = self._setup_tools()
        self.llm_with_tools = self._setup_model_with_tools()

        logger.info("="*60)
        logger.info(f"[SUCCESS] Engine ready! Tools: {len(self.tools)}, RAG={feature_flags.ENABLE_RAG}, Web={feature_flags.ENABLE_WEB_SEARCH}")
        logger.info("="*60)

    def _setup_tools(self) -> List[Callable]:
        """
        Setup tools as simple Python functions for bind_tools().

        LangChain automatically converts these to OpenAI function schemas.
        """
        tools = []

        # RAG Document Search
        if feature_flags.ENABLE_RAG:
            doc_list = self._get_document_list_summary()

            @tool(description=f"Cerca informazioni nei documenti caricati. Documenti disponibili: {doc_list}. Usa questo tool per domande su Develhope, Data & AI Week, Vincenzo Orrei.")
            async def ricerca_documenti(query: str) -> str:
                """Cerca informazioni nei documenti caricati."""
                return await self._search_documents(query)

            tools.append(ricerca_documenti)
            logger.info(f"      [TOOL] RAG ({len(self.vector_store.list_all_documents())} docs)")

        # Web Search
        if feature_flags.ENABLE_WEB_SEARCH and api_keys.TAVILY_API_KEY:
            # Create Tavily instance
            self.tavily_search = TavilySearchResults(
                max_results=3,
                search_depth="basic",
                include_answer=True,
                include_raw_content=False,
                api_key=api_keys.TAVILY_API_KEY
            )

            @tool(description="Cerca informazioni aggiornate su internet tramite web search. Usa questo tool per notizie recenti, eventi attuali, o informazioni non presenti nei documenti caricati.")
            async def ricerca_web(query: str) -> str:
                """Cerca informazioni aggiornate su internet."""
                try:
                    # Tavily returns list of dicts, convert to string
                    results = self.tavily_search.invoke(query)
                    if isinstance(results, list):
                        formatted = "\n\n".join([f"- {r.get('content', '')}" for r in results if r.get('content')])
                        return formatted if formatted else "Nessun risultato trovato."
                    return str(results)
                except Exception as e:
                    logger.error(f"[WEB SEARCH ERROR] {e}")
                    return f"Errore nella ricerca web: {str(e)}"

            tools.append(ricerca_web)
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

    def _setup_history_aware_retriever(self):
        """
        Setup retriever history-aware che contestualizza query con chat history.

        Usa create_history_aware_retriever per:
        1. Prendere query + chat_history
        2. LLM reformula query in standalone question
        3. Retrieval con query contestualizzata

        Returns:
            History-aware retriever
        """
        # Create wrapper retriever per il nostro Retriever custom
        class CustomRetrieverWrapper(BaseRetriever):
            """Wrapper per Retriever custom → LangChain BaseRetriever."""

            retriever: Any  # Il nostro Retriever custom

            def _get_relevant_documents(
                self, query: str, *, run_manager: CallbackManagerForRetrieverRun
            ) -> List[Document]:
                """Retrieval documenti."""
                results = self.retriever.retrieve(query=query)

                # Convert results to LangChain Documents
                documents = []
                for res in results:
                    doc = Document(
                        page_content=res.get('document', ''),
                        metadata={
                            'source': res.get('source', 'unknown'),
                            'score': res.get('score', 0.0),
                            'doc_id': res.get('doc_id', '')
                        }
                    )
                    documents.append(doc)

                return documents

        # Create wrapper instance
        wrapped_retriever = CustomRetrieverWrapper(retriever=self.retriever)

        # Create contextualization prompt
        contextualize_prompt = ChatPromptTemplate.from_messages([
            ("system", prompts.CONTEXTUALIZE_QUERY_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        logger.debug("[SETUP] Creating history-aware retriever...")

        return create_history_aware_retriever(
            self.llm,
            wrapped_retriever,
            contextualize_prompt
        )

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

    def _setup_model_with_tools(self):
        """
        Bind tools to LLM for native function calling.

        Super simple: LangChain converts Python functions to OpenAI function schemas automatically.
        """
        logger.info("      Binding tools to LLM...")

        if not self.tools:
            logger.warning("      [WARN] No tools to bind!")
            return self.llm

        llm_with_tools = self.llm.bind_tools(self.tools)
        logger.info(f"      [OK] LLM ready with {len(self.tools)} tools (max_iter={agent_config.MAX_ITERATIONS}, verbose={agent_config.VERBOSE})")

        return llm_with_tools

    def _get_session_history(self, user_id: int) -> ChatMessageHistory:
        """
        Ottieni o crea ChatMessageHistory per user_id.

        Args:
            user_id: Telegram user ID

        Returns:
            ChatMessageHistory per questo utente
        """
        if user_id not in self.session_store:
            self.session_store[user_id] = ChatMessageHistory()
            logger.debug(f"[SESSION] Created new history for user {user_id}")

        return self.session_store[user_id]

    def _apply_summary_buffer(self, messages: List, max_tokens: int = None) -> List:
        """
        Applica summary buffer se conversazione troppo lunga.

        Strategia ibrida:
        - Se token < soglia: return tutti i messaggi
        - Se token > soglia:
            1. Mantieni ultimi N messaggi intatti
            2. Riassumi messaggi vecchi con LLM
            3. Return [SystemMessage(summary)] + recent_messages

        Args:
            messages: Lista messaggi chat
            max_tokens: Soglia token (default: da config)

        Returns:
            Lista messaggi ottimizzata
        """
        if max_tokens is None:
            max_tokens = memory_config.MAX_TOKENS_BEFORE_SUMMARY

        # Stima token approssimativa (1 parola ≈ 1.3 token)
        total_tokens = sum(len(str(m.content).split()) * 1.3 for m in messages)

        logger.debug(f"[MEMORY] Total tokens estimate: {int(total_tokens)}")

        if total_tokens <= max_tokens:
            logger.debug(f"[MEMORY] Under threshold, keeping all {len(messages)} messages")
            return messages

        # Conversazione troppo lunga → summary buffer
        recent_count = memory_config.RECENT_MESSAGES_TO_KEEP
        recent_messages = messages[-recent_count:]
        old_messages = messages[:-recent_count]

        if not old_messages:
            return messages

        logger.info(f"[SUMMARY BUFFER] Activated: {len(old_messages)} old + {len(recent_messages)} recent")

        try:
            # Crea testo da riassumere
            old_content = "\n".join([
                f"{m.type.upper()}: {str(m.content)[:200]}"
                for m in old_messages
            ])

            # Genera riassunto con LLM
            summary_llm = ChatOpenAI(
                model=memory_config.SUMMARY_MODEL,
                temperature=0.3,  # Più basso per riassunti fedeli
                openai_api_key=api_keys.OPENAI_API_KEY
            )

            summary_response = summary_llm.invoke([
                HumanMessage(content=prompts.SUMMARIZE_CONVERSATION_PROMPT.format(
                    conversation=old_content
                ))
            ])

            summary_message = SystemMessage(
                content=f"[CONVERSATION SUMMARY]\n\n{summary_response.content}\n\n[END SUMMARY - Recent messages below]"
            )

            result = [summary_message] + recent_messages

            new_tokens = sum(len(str(m.content).split()) * 1.3 for m in result)
            logger.info(f"[SUMMARY BUFFER] Compressed: {int(total_tokens)} → {int(new_tokens)} tokens")

            return result

        except Exception as e:
            logger.error(f"[SUMMARY BUFFER] Failed: {e}, returning recent messages only")
            return recent_messages

    async def _search_documents(self, query: str) -> str:
        """
        Tool function: History-aware RAG search.

        Usa history-aware retriever per contestualizzare query con chat history.
        La chat_history viene passata via self.current_chat_history (impostata da process_message).

        Args:
            query: Query dell'utente

        Returns:
            Risposta dai documenti
        """
        logger.debug(f"[RAG TOOL] '{query[:50]}...'")

        try:
            # Get current chat history (impostata da process_message)
            chat_history = getattr(self, 'current_chat_history', [])

            # Se abbiamo chat history, usa history-aware retriever
            if chat_history and hasattr(self, 'history_aware_retriever'):
                logger.debug(f"[RAG TOOL] Using history-aware retriever with {len(chat_history)} history messages")

                # History-aware retriever ritorna documenti
                results = await self.history_aware_retriever.ainvoke({
                    "input": query,
                    "chat_history": chat_history
                })

                if not results:
                    return prompts.RAG_NO_CONTEXT_PROMPT

                # Format context da risultati
                if hasattr(results, '__iter__') and not isinstance(results, str):
                    context = "\n\n".join([doc.page_content for doc in results])
                else:
                    context = str(results)

            else:
                # Fallback: retrieval normale senza history
                logger.debug(f"[RAG TOOL] Using standard retriever (no history)")
                results = self.retriever.retrieve(query=query, k=rag_config.TOP_K)

                if not results:
                    return prompts.RAG_NO_CONTEXT_PROMPT

                context = self.retriever.format_context(results)

            # Genera risposta con contesto
            augmented_prompt = prompts.RAG_QUERY_PROMPT.format(
                context=context,
                query=query
            )

            response_message = await self.llm.ainvoke([HumanMessage(content=augmented_prompt)])

            return response_message.content

        except Exception as e:
            logger.error(f"[RAG TOOL ERROR] {e}")
            import traceback
            traceback.print_exc()
            return f"Errore nella ricerca documenti: {str(e)}"

    async def process_message(
        self,
        user_message: str,
        user_id: int
    ) -> str:
        """
        Processing con function calling iterativo.

        Flow:
        1. Recupera memoria utente
        2. Costruisce messages list con system prompt + history + user message
        3. Loop iterativo (max MAX_ITERATIONS):
           - LLM decide se chiamare tool o rispondere
           - Se chiama tool: esegui, aggiungi risultato, continua
           - Se risponde: return risposta
        4. Salva interazione in memoria

        Args:
            user_message: Messaggio dell'utente
            user_id: Telegram user ID

        Returns:
            Risposta del bot
        """
        logger.info(f"[PROCESS] User {user_id}: '{user_message[:50]}...'")

        try:
            # Get session history for this user
            session_history = self._get_session_history(user_id)
            chat_history = list(session_history.messages)

            logger.debug(f"[MEMORY] {len(chat_history)} messages in history")

            # Apply summary buffer if conversation is too long
            chat_history_optimized = self._apply_summary_buffer(chat_history)

            # Set current chat history for tools (used by history-aware retriever)
            self.current_chat_history = chat_history_optimized

            # Build system prompt with context
            temporal_context = self._build_temporal_context()
            documents_context = self._build_documents_context()
            system_prompt = prompts.SYSTEM_PROMPT + temporal_context + documents_context

            # Initialize messages list for this request
            messages = [SystemMessage(content=system_prompt)]
            messages.extend(chat_history_optimized)
            messages.append(HumanMessage(content=user_message))

            # Iterative loop for tool calling
            for iteration in range(agent_config.MAX_ITERATIONS):
                if agent_config.VERBOSE:
                    logger.info(f"[ITERATION {iteration + 1}/{agent_config.MAX_ITERATIONS}]")

                # Call LLM with tools
                response = await self.llm_with_tools.ainvoke(messages)

                # Check if LLM wants to call tools
                if response.tool_calls:
                    if agent_config.VERBOSE:
                        logger.info(f"[TOOL CALLS] {len(response.tool_calls)} tool(s) requested:")
                        for tc in response.tool_calls:
                            logger.info(f"  - {tc['name']}({tc['args']})")

                    # Add AI message to conversation
                    messages.append(response)

                    # Execute each tool call
                    for tool_call in response.tool_calls:
                        tool_name = tool_call['name']
                        tool_args = tool_call['args']
                        tool_id = tool_call['id']

                        # Find and execute the tool
                        tool_result = await self._execute_tool(tool_name, tool_args)

                        if agent_config.VERBOSE:
                            logger.info(f"  ✓ {tool_name} → {tool_result[:100]}...")

                        # Add tool result to conversation
                        messages.append(ToolMessage(
                            content=tool_result,
                            tool_call_id=tool_id
                        ))

                    # Continue loop to let LLM process tool results
                    continue

                else:
                    # No tool calls - LLM has final answer
                    final_response = response.content

                    if agent_config.VERBOSE:
                        logger.info(f"[FINAL ANSWER] {len(final_response)} chars")

                    # Save interaction to session history
                    session_history.add_user_message(user_message)
                    session_history.add_ai_message(final_response)

                    logger.info(f"[SUCCESS] {len(final_response)} chars in {iteration + 1} iteration(s)")

                    # Clean up temporary variable
                    if hasattr(self, 'current_chat_history'):
                        delattr(self, 'current_chat_history')

                    return final_response

            # Max iterations reached
            logger.warning(f"[MAX ITERATIONS] Reached {agent_config.MAX_ITERATIONS}, forcing response")
            final_response = response.content if hasattr(response, 'content') else "Mi dispiace, non ho potuto completare la richiesta."

            # Save interaction anyway
            session_history.add_user_message(user_message)
            session_history.add_ai_message(final_response)

            # Clean up temporary variable
            if hasattr(self, 'current_chat_history'):
                delattr(self, 'current_chat_history')

            return final_response

        except Exception as e:
            logger.error(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
            return f"Mi dispiace, si è verificato un errore: {str(e)[:200]}"

    async def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool

        Returns:
            Tool result as string
        """
        try:
            # Find the tool in self.tools
            for tool in self.tools:
                if tool.name == tool_name:
                    # Execute the tool (all tools are async)
                    result = await tool.ainvoke(tool_args)
                    return str(result)

            # Tool not found
            logger.error(f"[TOOL ERROR] Tool '{tool_name}' not found")
            return f"Errore: Tool '{tool_name}' non trovato"

        except Exception as e:
            logger.error(f"[TOOL ERROR] {tool_name}: {e}")
            import traceback
            traceback.print_exc()
            return f"Errore nell'esecuzione di {tool_name}: {str(e)}"

    def refresh_agent(self):
        """
        Ricrea tools e LLM binding con contesto documenti aggiornato.

        Chiamare dopo upload/eliminazione documenti.
        Mantiene nome 'refresh_agent' per compatibilità con handlers.
        """
        logger.info("[REFRESH] Rebuilding tools and LLM binding...")

        try:
            self.tools = self._setup_tools()
            self.llm_with_tools = self._setup_model_with_tools()

            logger.info("[REFRESH] Complete!")
            logger.info(f"[REFRESH] Tools: {len(self.tools)}, Docs: {len(self.vector_store.list_all_documents())}")

        except Exception as e:
            logger.error(f"[REFRESH] Failed: {e}")
            import traceback
            traceback.print_exc()

    def clear_memory(self, user_id: int):
        """Cancella memoria conversazione per user_id."""
        if user_id in self.session_store:
            del self.session_store[user_id]
            logger.info(f"[MEMORY] Cleared history for user {user_id}")
        else:
            logger.warning(f"[MEMORY] No history found for user {user_id}")


if __name__ == "__main__":
    print("LangChain Core Engine")
    print("Requires: Vector store + API keys")
    print("Run: python main.py")
