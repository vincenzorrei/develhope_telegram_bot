"""
Quick test per verificare che async ainvoke funzioni correttamente.
"""
import asyncio
from bot_engine import LangChainEngine
from src.rag.vector_store import VectorStoreManager

async def test_async_processing():
    """Test async message processing"""
    print("🧪 Testing async message processing...")

    # Initialize components
    vector_store = VectorStoreManager()
    engine = LangChainEngine(vector_store)

    # Test simple query
    print("\n📝 Test 1: Simple query (no RAG, no web)")
    response = await engine.process_message(
        user_message="Ciao, come stai?",
        user_id=999999
    )
    print(f"✅ Response received: {response[:100]}...")

    # Test RAG query
    print("\n📝 Test 2: RAG query")
    response = await engine.process_message(
        user_message="Quali sono le informazioni nel documento caricato?",
        user_id=999999
    )
    print(f"✅ Response received: {response[:100]}...")

    print("\n✅ All async tests passed!")

if __name__ == "__main__":
    asyncio.run(test_async_processing())
