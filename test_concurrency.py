"""
Test concorrenza per verificare miglioramento capacità con asyncio.
"""
import asyncio
import time
from bot_engine import LangChainEngine
from src.rag.vector_store import VectorStoreManager

async def simulate_user_query(engine, user_id, query, delay=0):
    """Simula query di un singolo utente"""
    if delay:
        await asyncio.sleep(delay)

    start = time.time()
    response = await engine.process_message(
        user_message=query,
        user_id=user_id
    )
    elapsed = time.time() - start

    print(f"✅ User {user_id}: {elapsed:.2f}s - {response[:80]}...")
    return elapsed

async def test_concurrent_users():
    """Test gestione utenti concorrenti"""
    print("🧪 Testing concurrent user handling...")
    print("=" * 60)

    # Initialize
    vector_store = VectorStoreManager()
    engine = LangChainEngine(vector_store)

    # Test 1: Sequential (baseline)
    print("\n📊 Test 1: SEQUENTIAL (3 users, one at a time)")
    start = time.time()
    for i in range(3):
        await simulate_user_query(
            engine,
            user_id=1000 + i,
            query="Ciao, puoi aiutarmi?"
        )
    sequential_time = time.time() - start
    print(f"⏱️  Total sequential time: {sequential_time:.2f}s")

    # Test 2: Concurrent (async benefit)
    print(f"\n📊 Test 2: CONCURRENT (3 users, parallel)")
    start = time.time()
    tasks = [
        simulate_user_query(
            engine,
            user_id=2000 + i,
            query=f"Domanda utente {i}",
            delay=i * 0.1  # Stagger requests slightly
        )
        for i in range(3)
    ]
    results = await asyncio.gather(*tasks)
    concurrent_time = time.time() - start
    print(f"⏱️  Total concurrent time: {concurrent_time:.2f}s")

    # Analysis
    print(f"\n" + "=" * 60)
    print(f"📈 RESULTS:")
    print(f"   Sequential: {sequential_time:.2f}s")
    print(f"   Concurrent: {concurrent_time:.2f}s")
    improvement = ((sequential_time - concurrent_time) / sequential_time) * 100
    print(f"   Improvement: {improvement:.1f}%")
    print(f"   Speedup: {sequential_time / concurrent_time:.2f}x")

    if improvement > 30:
        print(f"\n✅ Async is working! {improvement:.1f}% faster")
    else:
        print(f"\n⚠️  Limited improvement. Possible bottleneck?")

    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_concurrent_users())
