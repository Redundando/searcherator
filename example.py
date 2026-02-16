from searcherator import Searcherator
import asyncio
import time

async def main():
    # Test batch processing with rate limiting
    queries = [f"Python topic {i}" for i in range(50)]
    
    print(f"Starting {len(queries)} searches concurrently...")
    print(f"Rate limiter will allow max 20 concurrent requests\n")
    
    start_time = time.time()
    
    try:
        # Create all search instances
        searches = [Searcherator(query, num_results=3) for query in queries]
        
        # Run all searches concurrently (rate limiter will queue them)
        results = await asyncio.gather(*[s.search_result() for s in searches], return_exceptions=True)
    finally:
        # Close the shared session when done
        await Searcherator.close_session()
    
    elapsed = time.time() - start_time
    
    # Count successes and failures
    successes = sum(1 for r in results if isinstance(r, dict))
    failures = sum(1 for r in results if isinstance(r, Exception))
    
    # Show failure details if any
    if failures > 0:
        print(f"\nFailure Details:")
        for i, (query, result) in enumerate(zip(queries, results)):
            if isinstance(result, Exception):
                print(f"  {i+1}. '{query}' - {type(result).__name__}: {result}")
    
    print(f"\n{'='*60}")
    print(f"Completed {len(queries)} searches in {elapsed:.2f} seconds")
    print(f"Successes: {successes}")
    print(f"Failures: {failures}")
    print(f"Average: {elapsed/len(queries):.2f}s per search")
    
    # Show rate limit info from last search
    if searches:
        last = searches[-1]
        print(f"\nFinal Rate Limit Status:")
        print(f"  Per Second - Remaining: {last.rate_remaining_per_second}/{last.rate_limit_per_second}")
        print(f"  Per Month  - Remaining: {last.rate_remaining_per_month}/{last.rate_limit_per_month}")
    
    # Display first 5 search results
    print(f"\n{'='*60}")
    print(f"Sample Results (first 5 searches):\n")
    for i, (query, result) in enumerate(zip(queries[:5], results[:5])):
        if isinstance(result, dict):
            web_results = result.get('web', {}).get('results', [])
            print(f"{i+1}. Query: '{query}'")
            print(f"   Found {len(web_results)} results:")
            for j, item in enumerate(web_results, 1):
                print(f"     {j}. {item.get('title', 'N/A')}")
                print(f"        {item.get('url', 'N/A')}")
            print()
        else:
            print(f"{i+1}. Query: '{query}' - Error: {result}\n")

if __name__ == "__main__":
    asyncio.run(main())
