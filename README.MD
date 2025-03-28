# Searcherator

Searcherator is a Python package that provides a convenient way to perform web searches using the Brave Search API with built-in caching capabilities.

## Installation

```bash
pip install searcherator
```

## Requirements

- Python 3.8+
- Brave Search API key

## Usage

```python
from searcherator import Searcherator
import asyncio

async def main():
    # Basic search in English (US)
    search = Searcherator("Python programming language")
    
    # Get URLs from search results
    urls = await search.urls()
    print(urls)
    
    # German search with more results
    german_search = Searcherator(
        "Zusammenfassung Buch 'Demian' von 'Hermann Hesse'",
        language="de",
        country="de",
        num_results=10
    )
    
    # Print full search results
    await german_search.print()

if __name__ == "__main__":
    asyncio.run(main())
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
    clear_cache: bool = False,
    ttl: int = 7
)
```

#### Parameters

- `search_term`: The query string to search for
- `num_results`: Maximum number of results to return (default: 5)
- `country`: Country code for search results (default: "us")
- `language`: Language code for search results (default: "en")
- `api_key`: Brave Search API key (default: None, will try to use BRAVE_API_KEY environment variable)
- `clear_cache`: Whether to clear existing cached results (default: False)
- `ttl`: Time-to-live for cached results in days (default: 7)

#### Methods

- `async urls() -> list[str]`: Returns a list of URLs from the search results
- `async search_result() -> dict`: Returns the full search results as a dictionary
- `async print()`: Prints the full search results in a formatted way

## Authentication

Set your Brave Search API key as an environment variable:

```bash
export BRAVE_API_KEY="your-api-key-here"
```

Alternatively, provide the API key directly when initializing the Searcherator:

```python
search = Searcherator("My search term", api_key="your-api-key-here")
```

## License

MIT License

## Author

Arved Klöhn - [GitHub](https://github.com/Redundando/)