---
Package: ghostscraper
Version: 0.4.3
Source: https://pypi.org/project/ghostscraper/
Fetched: 2026-02-22 14:15:53
---

# Ghostscraper

A Playwright-based web scraper with persistent caching, automatic browser installation, and multiple output formats.

## Changelog

### v0.4.1 (Latest)
- Added `load_strategies` parameter to customize the loading strategy chain
- Defaults to `["load", "networkidle", "domcontentloaded"]` but can be overridden to skip slow strategies

### v0.4.0
- Added `on_progress` callback for real-time scraping progress events
- Supports both sync and async callbacks
- Callbacks fire at key events: browser ready, loading strategy, retries, page loaded, errors, and batch lifecycle

### v0.3.0
- Added DynamoDB L2 cache support for cross-machine cache sharing
- Simplified logging to boolean (`logging=True/False`)
- Added `dynamodb_table` parameter to `GhostScraper` and `scrape_many()`

### v0.2.1
- Fixed RuntimeError when browser installation check runs within an active event loop
- Improved compatibility with Linux and other Unix-like systems

### v0.2.0
- Initial stable release

## Features

- **Headless Browser Scraping**: Uses Playwright for reliable scraping of JavaScript-heavy websites
- **Parallel Scraping**: Scrape multiple URLs concurrently with shared browser instances
- **Persistent Caching**: Stores scraped data between runs for improved performance
- **DynamoDB L2 Cache**: Optional cross-machine cache sharing via AWS DynamoDB
- **Automatic Browser Installation**: Self-installs required browsers
- **Configurable Loading Strategies**: Override the default strategy chain per-scraper to skip slow strategies
- **Multiple Output Formats**: HTML, Markdown, Plain Text, BeautifulSoup, SEO metadata
- **Progress Callbacks**: Optional `on_progress` callback for real-time scraping events
- **Boolean Logging**: Enable/disable logging with `logging=True/False`
- **Error Handling**: Robust retry mechanism with exponential backoff
- **Asynchronous API**: Modern async/await interface
- **Type Hints**: Full type annotation support for better IDE integration

## Installation

```bash
pip install ghostscraper
```

## Basic Usage

### Simple Scraping

```python
import asyncio
from ghostscraper import GhostScraper

async def main():
    # Initialize the scraper
    scraper = GhostScraper(url="https://example.com")
    
    # Get the HTML content
    html = await scraper.html()
    print(html)
    
    # Get plain text content
    text = await scraper.text()
    print(text)
    
    # Get markdown version
    markdown = await scraper.markdown()
    print(markdown)

# Run the async function
asyncio.run(main())
```

### Batch Scraping (Parallel)

```python
import asyncio
from ghostscraper import GhostScraper

async def main():
    urls = [
        "https://example.com",
        "https://www.python.org",
        "https://github.com"
    ]
    
    # Scrape multiple URLs in parallel with a shared browser
    scrapers = await GhostScraper.scrape_many(
        urls=urls,
        max_concurrent=3,
        logging=True
    )
    
    # Access results from each scraper
    for scraper in scrapers:
        text = await scraper.text()
        print(f"{scraper.url}: {len(text)} characters")

asyncio.run(main())
```

### With Custom Options

```python
import asyncio
from ghostscraper import GhostScraper

async def main():
    # Initialize with custom options
    scraper = GhostScraper(
        url="https://example.com",
        browser_type="firefox",  # Use Firefox instead of default Chromium
        headless=False,          # Show the browser window
        load_timeout=60000,      # 60 seconds timeout
        clear_cache=True,        # Clear previous cache
        ttl=1,                   # Cache for 1 day
        logging=True             # Enable logging
    )
    
    # Get the HTML content
    html = await scraper.html()
    print(html)

asyncio.run(main())
```

### With DynamoDB Cache

```python
import asyncio
from ghostscraper import GhostScraper

async def main():
    # Single scraper with DynamoDB L2 cache
    scraper = GhostScraper(
        url="https://example.com",
        dynamodb_table="my-cache-table"  # Requires AWS credentials
    )
    html = await scraper.html()

    # Batch scraping with DynamoDB
    scrapers = await GhostScraper.scrape_many(
        urls=["https://example.com", "https://python.org"],
        dynamodb_table="my-cache-table"
    )

asyncio.run(main())
```

## API Reference

### GhostScraper

The main class for web scraping with persistent caching.

#### Constructor

```python
GhostScraper(
    url: str = "",
    clear_cache: bool = False,
    ttl: int = 999,
    markdown_options: Optional[Dict[str, Any]] = None,
    logging: bool = True,
    dynamodb_table: Optional[str] = None,
    on_progress: Optional[Callable] = None,
    **kwargs
)
```

**Parameters**:
- `url` (str): The URL to scrape.
- `clear_cache` (bool): Whether to clear existing cache on initialization.
- `ttl` (int): Time-to-live for cached data in days.
- `markdown_options` (Dict[str, Any]): Options for HTML to Markdown conversion.
- `logging` (bool): Enable/disable logging. Default: True.
- `dynamodb_table` (str): DynamoDB table name for cross-machine caching. Default: None.
- `on_progress` (Callable, optional): Callback fired at key scraping events. Accepts both sync and async callables. Default: None.
- `**kwargs`: Additional options passed to PlaywrightScraper.

**Playwright Options (passed via kwargs)**:
- `browser_type` (str): Browser engine to use, one of "chromium", "firefox", or "webkit". Default: "chromium".
- `headless` (bool): Whether to run the browser in headless mode. Default: True.
- `browser_args` (Dict[str, Any]): Additional arguments to pass to the browser.
- `context_args` (Dict[str, Any]): Additional arguments to pass to the browser context.
- `max_retries` (int): Maximum number of retry attempts. Default: 3.
- `backoff_factor` (float): Factor for exponential backoff between retries. Default: 2.0.
- `network_idle_timeout` (int): Milliseconds to wait for network to be idle. Default: 10000 (10 seconds).
- `load_timeout` (int): Milliseconds to wait for page to load. Default: 30000 (30 seconds).
- `wait_for_selectors` (List[str]): CSS selectors to wait for before considering page loaded.
- `load_strategies` (List[str]): Loading strategies to try in order. Default: `["load", "networkidle", "domcontentloaded"]`.

#### Methods

##### `async html() -> str`

Returns the raw HTML content of the page.

##### `async response_code() -> int`

Returns the HTTP response code from the page request.

##### `async markdown() -> str`

Returns the page content converted to Markdown.

##### `async article() -> newspaper.Article`

Returns a newspaper.Article object with parsed content.

##### `async text() -> str`

Returns the plain text content of the page.

##### `async authors() -> str`

Returns the detected authors of the content.

##### `async soup() -> BeautifulSoup`

Returns a BeautifulSoup object for the page.

##### `async seo() -> dict`

Returns a dictionary of SEO metadata parsed from the page HTML. No additional network request is made. All keys are omitted if the corresponding tag is absent.

```python
{
    "title": str,           # <title>
    "description": str,     # <meta name="description">
    "canonical": str,       # <link rel="canonical">
    "robots": {             # <meta name="robots"> — raw directives as keys, e.g. {"noindex": True}
        "noindex": True,
        "nofollow": True,
    },
    "googlebot": { ... },   # <meta name="googlebot">, same shape as robots, omitted if absent
    "og": {                 # <meta property="og:*"> tags, keyed by suffix
        "title": str,
        "description": str,
        "image": str,
        "url": str,
    },
    "twitter": { ... },     # <meta name="twitter:*"> tags, same pattern
    "hreflang": {           # <link rel="alternate" hreflang="..."> — values are lists
        "en-us": ["https://..."],
        "de": ["https://..."],
    }
}
```

##### `@classmethod async scrape_many(urls: List[str], max_concurrent: int = 5, logging: bool = True, **kwargs) -> List[GhostScraper]`

Scrape multiple URLs in parallel using a shared browser instance.

**Parameters**:
- `urls` (List[str]): List of URLs to scrape.
- `max_concurrent` (int): Maximum number of concurrent page loads. Default: 5.
- `logging` (bool): Enable/disable logging. Default: True.
- `on_progress` (Callable, optional): Callback fired at key scraping events. Default: None.
- `**kwargs`: Additional options passed to GhostScraper and PlaywrightScraper.

**Returns**: List of GhostScraper instances with cached results.

### PlaywrightScraper

Low-level browser automation class used by GhostScraper.

#### Constructor

```python
PlaywrightScraper(
    url: str = "",
    browser_type: Literal["chromium", "firefox", "webkit"] = "chromium",
    headless: bool = True,
    browser_args: Optional[Dict[str, Any]] = None,
    context_args: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    network_idle_timeout: int = 10000,
    load_timeout: int = 30000,
    wait_for_selectors: Optional[List[str]] = None,
    logging: bool = True,
    load_strategies: Optional[List[str]] = None
)
```

**Parameters**: Same as listed in GhostScraper kwargs above.

#### Methods

##### `async fetch() -> Tuple[str, int]`

Fetches the page and returns a tuple of (html_content, status_code).

##### `async fetch_url(url: str) -> Tuple[str, int]`

Fetches a specific URL using the shared browser instance.

##### `async fetch_many(urls: List[str], max_concurrent: int = 5) -> List[Tuple[str, int]]`

Fetches multiple URLs in parallel using a shared browser instance with concurrency control.

##### `async fetch_and_close() -> Tuple[str, int]`

Fetches the page, closes the browser, and returns a tuple of (html_content, status_code).

##### `async close() -> None`

Closes the browser and playwright resources.

##### `async check_and_install_browser() -> bool`

Checks if the required browser is installed, and installs it if not. Returns True if successful.

## Progress Callbacks

Pass an `on_progress` callable to receive real-time events during scraping. Both sync and async callables are supported.

```python
# Sync callback
scraper = GhostScraper(url="https://example.com", on_progress=lambda e: print(e["event"]))

# Async callback
async def on_progress(event):
    await queue.put(event)

scraper = GhostScraper(url="https://example.com", on_progress=on_progress)

# Batch scraping
scrapers = await GhostScraper.scrape_many(urls=urls, on_progress=on_progress)
```

Each event is a dict with an `event` key and a `ts` Unix timestamp. Additional fields depend on the event type:

| event | fields | notes |
|---|---|---|
| `started` | `url` | fired before fetch begins |
| `browser_installing` | `browser` | first-run only; sync callback only |
| `browser_ready` | `browser` | browser check passed |
| `loading_strategy` | `url`, `strategy`, `attempt`, `max_retries`, `timeout` | see loading strategies below |
| `retry` | `url`, `attempt`, `max_retries` + optional `reason`, `status_code` | only fires when another attempt follows |
| `page_loaded` | `url`, `completed`, `total`, `status_code` | fires on success or error status |
| `error` | `url`, `message` | unhandled exception during fetch |
| `batch_started` | `total`, `to_fetch`, `cached` | `scrape_many` only |
| `batch_done` | `total` | `scrape_many` only |

### Loading Strategies

By default, GhostScraper tries three Playwright loading strategies in order, falling back if the previous times out:

- `load` — waits for the `load` event (default, works for most sites)
- `networkidle` — waits until no network activity for 500ms (better for JS-heavy pages)
- `domcontentloaded` — waits only for HTML parsing (fastest fallback, least complete)

If a URL triggers multiple `loading_strategy` events, it means earlier strategies timed out and fell back. If all strategies fail, the attempt is retried up to `max_retries` times with exponential backoff.

Use `load_strategies` to override the chain. This is useful when you know a site will always time out on certain strategies:

```python
# Skip straight to domcontentloaded
scrapers = await GhostScraper.scrape_many(
    urls=urls,
    load_strategies=["domcontentloaded"]
)

# Or set a global default
from ghostscraper import ScraperDefaults
ScraperDefaults.LOAD_STRATEGIES = ["domcontentloaded"]
```

## Advanced Usage

### Configuring Global Defaults

```python
from ghostscraper import ScraperDefaults

# Modify defaults for all future scraper instances
ScraperDefaults.MAX_CONCURRENT = 20
ScraperDefaults.LOGGING = False
ScraperDefaults.HEADLESS = False
ScraperDefaults.LOAD_TIMEOUT = 30000
ScraperDefaults.DYNAMODB_TABLE = "my-cache-table"
```

### Batch Scraping with Options

```python
import asyncio
from ghostscraper import GhostScraper

async def main():
    urls = [f"https://example.com/page{i}" for i in range(1, 11)]
    
    # Scrape with custom options
    scrapers = await GhostScraper.scrape_many(
        urls=urls,
        max_concurrent=5,
        browser_type="chromium",
        headless=True,
        load_timeout=60000,
        ttl=7,  # Cache for 7 days
        logging=True
    )
    
    # Process results
    for scraper in scrapers:
        markdown = await scraper.markdown()
        print(f"Scraped {scraper.url}")

asyncio.run(main())
```

### Custom Browser Configurations

```python
from ghostscraper import GhostScraper

# Set up a browser with custom viewport size and user agent
browser_context_args = {
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

scraper = GhostScraper(
    url="https://example.com",
    context_args=browser_context_args
)
```

### Waiting for Dynamic Content

```python
from ghostscraper import GhostScraper

# Wait for specific elements to load before considering the page ready
scraper = GhostScraper(
    url="https://example.com/dynamic-page",
    wait_for_selectors=["#content", ".product-list", "button.load-more"]
)
```

### Custom Markdown Options

```python
from ghostscraper import GhostScraper

# Customize the markdown conversion
markdown_options = {
    "ignore_links": True,
    "ignore_images": True,
    "bullet_character": "*"
}

scraper = GhostScraper(
    url="https://example.com",
    markdown_options=markdown_options
)
```

### Browser Management

```python
from ghostscraper import check_browser_installed, install_browser
import asyncio

async def setup_browsers():
    # Check if browsers are installed
    chromium_installed = await check_browser_installed("chromium")
    firefox_installed = await check_browser_installed("firefox")
    
    # Install browsers if needed
    if not chromium_installed:
        install_browser("chromium")
    
    if not firefox_installed:
        install_browser("firefox")

asyncio.run(setup_browsers())
```

## Performance Considerations

- Use caching effectively by setting appropriate TTL values
- Use `scrape_many()` for batch scraping to share browser instances and reduce memory usage
- Adjust `max_concurrent` based on your system resources and target website rate limits
- Consider browser memory usage when scraping multiple pages
- For best performance, use "chromium" as it's generally the fastest engine
- Use `logging=False` for production to minimize overhead

## Error Handling

GhostScraper uses a progressive loading strategy:
1. First attempts with `load` (fast, works for most sites)
2. Falls back to `networkidle` if timeout occurs (better for JS-heavy pages)
3. Finally tries `domcontentloaded` (fastest but least complete)

If all strategies fail, it will retry up to `max_retries` times with exponential backoff.

## License

This project is licensed under the MIT License.

## Dependencies

- playwright
- beautifulsoup4
- html2text
- newspaper4k
- python-slugify
- logorator
- cacherator
- lxml_html_clean

## Contributing

Contributions are welcome! Visit the GitHub repository: https://github.com/Redundando/ghostscraper
