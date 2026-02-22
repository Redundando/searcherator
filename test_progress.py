import asyncio
from searcherator import Searcherator


async def main():
    # Test with sync callback - clear cache to see both scenarios
    search = Searcherator(
        "Python programming",
        num_results=3,
        clear_cache=True,
        on_progress=lambda e: print(f"Event: {e}")
    )
    
    # First call - should hit API
    print("First call:")
    await search.search_result()
    
    # Second call - should be cached
    print("\nSecond call:")
    await search.search_result()
    
    await Searcherator.close_session()


if __name__ == "__main__":
    asyncio.run(main())
