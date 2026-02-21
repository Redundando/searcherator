# Searcherator

Searcherator is a Python package that provides a convenient way to perform web searches using the Brave Search API with built-in caching, automatic rate limiting, and efficient batch processing capabilities.

## Features

- Async/await support for modern Python applications
- Automatic caching with configurable TTL
- Optional DynamoDB backend for cross-machine cache sharing
- Built-in rate limiting to respect API quotas
- Efficient batch processing for multiple concurrent searches
- Support for multiple languages and countries
- Comprehensive exception hierarchy for robust error handling
- Real-time rate limit tracking and monitoring

## Installation

```bash
pip install searcherator
```

## Requirements

- Python 3.8+
- Brave Search API key ([Get one here](https://brave.com/search/api/))

## Quick Start

```python
from searcherator import Searcherator
import asyncio

async def main():
    # Basic search
    search = Searcherator("Python programming")
    
    # Get URLs from search results
    urls = await search.urls()
    print(urls)
    
    # Get detailed results
    results = await search.detailed_search_result()
    for result in results:
        print(f"{result['title']}: {result['url']}")
    
    # Clean up
    await Searcherator.close_session()

if __name__ == "__main__":
    asyncio.run(main())
```

## Usage Examples

### Basic Search

```python
from searcherator import Searcherator
import asyncio

async def main():
    search = Searcherator("Python tutorials", num_results=10)
    results = await search.search_result()
    print(results)
    await Searcherator.close_session()

asyncio.run(main())
```

### Localized Search

```python
# German search
german_search = Searcherator(
    "Zusammenfassung Buch 'Demian' von 'Hermann Hesse'",
    language="de",
    country="de",
    num_results=10
)
results = await german_search.search_result()
```

### Batch Processing

```python
import asyncio
from searcherator import Searcherator

async def batch_search():
    queries = ["Python", "JavaScript", "Rust", "Go", "TypeScript"]
    
    try:
        # Create search instances
        searches = [Searcherator(q, num_results=5) for q in queries]
        
        # Run all searches concurrently (rate limiting handled automatically)
        results = await asyncio.gather(
            *[s.search_result() for s in searches],
            return_exceptions=True
        )
        
        # Process results
        for query, result in zip(queries, results):
            if isinstance(result, dict):
                print(f"{query}: {len(result.get('web', {}).get('results', []))} results")
    finally:
        await Searcherator.close_session()

asyncio.run(batch_search())
```

### Error Handling

```python
from searcherator import (
    Searcherator,
    SearcheratorAuthError,
    SearcheratorRateLimitError,
    SearcheratorTimeoutError,
    SearcheratorAPIError
)

async def safe_search():
    try:
        search = Searcherator("Python", timeout=10)
        results = await search.search_result()
    except SearcheratorAuthError:
        print("Invalid API key")
    except SearcheratorRateLimitError as e:
        print(f"Rate limited. Resets in {e.reset_per_second}s")
    except SearcheratorTimeoutError:
        print("Request timed out")
    except SearcheratorAPIError as e:
        print(f"API error: {e.status_code} - {e.message}")
    finally:
        await Searcherator.close_session()
```

### Monitoring Rate Limits

```python
search = Searcherator("Python")
results = await search.search_result()

print(f"Rate limit (per second): {search.rate_limit_per_second}")
print(f"Remaining (per second): {search.rate_remaining_per_second}")
print(f"Rate limit (per month): {search.rate_limit_per_month}")
print(f"Remaining (per month): {search.rate_remaining_per_month}")
```

## API Reference

### Searcherator

```python
Searcherator(
    search_term: str = "",
    num_results: int = 5,
    country: str | None = "us",
    language: str | None = "en",
    api_key: str | None = None,
    spellcheck: bool = False,
    timeout: int = 30,
    clear_cache: bool = False,
    ttl: int = 7,
    logging: bool = False,
    dynamodb_table: str | None = None
)
```

#### Parameters

- **search_term** (str): The query string to search for
- **num_results** (int): Maximum number of results to return (default: 5)
- **country** (str): Country code for search results (default: "us")
- **language** (str): Language code for search results (default: "en")
- **api_key** (str): Brave Search API key (default: None, uses BRAVE_API_KEY environment variable)
- **spellcheck** (bool): Enable spell checking on queries (default: False)
- **timeout** (int): Request timeout in seconds (default: 30)
- **clear_cache** (bool): Clear existing cached results (default: False)
- **ttl** (int): Time-to-live for cached results in days (default: 7)
- **logging** (bool): Enable cache operation logging (default: False)
- **dynamodb_table** (str): DynamoDB table name for cross-machine cache sharing (default: None)

#### Methods

##### `async search_result() -> dict`
Returns the full search results as a dictionary from the Brave Search API.

##### `async urls() -> list[str]`
Returns a list of URLs from the search results.

##### `async detailed_search_result() -> list[dict]`
Returns detailed information for each search result including title, URL, description, and metadata.

##### `async print() -> None`
Pretty prints the full search results.

##### `@classmethod async close_session()`
Closes the shared aiohttp session. Call this when done with all searches.

## Authentication

Set your Brave Search API key as an environment variable:

```bash
# Linux/macOS
export BRAVE_API_KEY="your-api-key-here"

# Windows
set BRAVE_API_KEY=your-api-key-here
```

Or provide it directly:

```python
search = Searcherator("My search term", api_key="your-api-key-here")
```

## Exception Hierarchy

```
SearcheratorError (base exception)
├── SearcheratorAuthError (authentication failures)
├── SearcheratorRateLimitError (rate limit exceeded)
├── SearcheratorTimeoutError (request timeout)
└── SearcheratorAPIError (other API errors)
```

## Rate Limiting

Searcherator automatically handles rate limiting to respect Brave Search API quotas:

- **Automatic throttling** - Requests are automatically spaced to stay within limits
- **Concurrent control** - Built-in semaphore limits concurrent requests
- **Rate limit tracking** - Monitor your usage via instance attributes

The default configuration safely handles up to ~13 requests per second, well under typical API limits.

## Caching

Results are automatically cached to disk:

- **Location**: `data/search/` directory
- **Format**: JSON files
- **TTL**: Configurable (default: 7 days)
- **Cache key**: Based on search term, language, country, and num_results

### DynamoDB Backend (Optional)

Enable cross-machine cache sharing via DynamoDB:

```python
search = Searcherator(
    "Python tutorials",
    dynamodb_table="my-search-cache"
)
results = await search.search_result()
```

**How it works:**
- **L1 (local JSON)**: Checked first for instant access
- **L2 (DynamoDB)**: Checked on L1 miss, synced across machines
- **No table specified**: Works as local-only cache

**Requirements:**
- Install boto3: `pip install boto3`
- AWS credentials configured (environment variables, IAM role, or ~/.aws/credentials)
- DynamoDB table auto-created if missing (requires IAM permissions)

To disable caching for a specific search:

```python
search = Searcherator("Python", clear_cache=True, ttl=0)
```

## Best Practices

1. **Always close the session** when done:
   ```python
   try:
       # Your searches
   finally:
       await Searcherator.close_session()
   ```

2. **Use batch processing** for multiple searches:
   ```python
   results = await asyncio.gather(*[s.search_result() for s in searches])
   ```

3. **Handle exceptions** appropriately:
   ```python
   try:
       results = await search.search_result()
   except SearcheratorRateLimitError:
       # Wait and retry
   ```

4. **Monitor rate limits** for high-volume applications:
   ```python
   if search.rate_remaining_per_month < 1000:
       # Alert or throttle
   ```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest test_searcherator.py -v

# Run with coverage
pip install pytest-cov
pytest test_searcherator.py --cov=searcherator --cov-report=html
```

## License

MIT License

## Links

- **GitHub**: [https://github.com/Redundando/searcherator](https://github.com/Redundando/searcherator)
- **PyPI**: [https://pypi.org/project/searcherator/](https://pypi.org/project/searcherator/)
- **Issues**: [https://github.com/Redundando/searcherator/issues](https://github.com/Redundando/searcherator/issues)

## Author

Arved Klöhn - [GitHub](https://github.com/Redundando/)