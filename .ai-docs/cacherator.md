---
Package: cacherator
Version: 1.2.8
Source: https://pypi.org/project/cacherator/
Fetched: 2026-02-22 14:15:53
---

# Cacherator

**Persistent JSON caching for Python with async support** - Cache function results and object state effortlessly.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Cacherator is a Python library that provides persistent JSON-based caching for class state and function results. It enables developers to cache expensive operations with minimal configuration, supporting both synchronous and asynchronous functions.

### Key Features

- **Zero-configuration caching** - Simple inheritance and decorator pattern
- **Async/await support** - Native support for asynchronous functions
- **Persistent storage** - Cache survives program restarts
- **TTL (Time-To-Live)** - Automatic cache expiration
- **Selective caching** - Fine-grained control over what gets cached
- **Cache management** - Built-in methods for inspection and clearing
- **Cache status tracking** - Per-call hit/miss detection with L1/L2 source
- **Flexible logging** - Global and per-instance control
- **DynamoDB backend** - Optional L2 cache for cross-machine sharing

## Installation

```bash
pip install cacherator
```

### Optional: DynamoDB Support

For cross-machine cache sharing via DynamoDB:

```bash
pip install boto3
```

## Quick Start

### Basic Function Caching

```python
from cacherator import JSONCache, Cached
import time

class Calculator(JSONCache):
    def __init__(self):
        super().__init__(data_id="calc")
    
    @Cached()
    def expensive_calculation(self, x, y):
        time.sleep(2)  # Simulate expensive operation
        return x ** y

calc = Calculator()
result = calc.expensive_calculation(2, 10)  # Takes 2 seconds
result = calc.expensive_calculation(2, 10)  # Instant!
```

### Async Function Caching

```python
class APIClient(JSONCache):
    @Cached(ttl=1)  # Cache for 1 day
    async def fetch_user(self, user_id):
        # Expensive API call
        response = await api.get(f"/users/{user_id}")
        return response.json()

client = APIClient()
user = await client.fetch_user(123)  # API call
user = await client.fetch_user(123)  # Cached!
```

### State Persistence

```python
class GameState(JSONCache):
    def __init__(self, game_id):
        super().__init__(data_id=f"game_{game_id}")
        if not hasattr(self, "score"):
            self.score = 0
            self.level = 1
    
    def add_points(self, points):
        self.score += points
        self.json_cache_save()

# Session 1
game = GameState("player1")
game.add_points(100)

# Session 2 (after restart)
game = GameState("player1")
print(game.score)  # 100 - persisted!
```

## Advanced Usage

### DynamoDB Backend (Cross-Machine Cache Sharing)

Enable optional DynamoDB L2 cache for sharing cache across multiple machines:

```python
from cacherator import JSONCache, Cached

class WebScraper(JSONCache):
    def __init__(self):
        super().__init__(dynamodb_table='my-cache-table')
    
    @Cached(ttl=7)
    def scrape_expensive_data(self, url):
        # Expensive operation
        return fetch_data(url)

# On machine 1 (laptop)
scraper = WebScraper()
data = scraper.scrape_expensive_data("https://example.com")  # Scrapes and caches

# On machine 2 (EC2 instance) - same code
scraper = WebScraper()
data = scraper.scrape_expensive_data("https://example.com")  # Uses cached data!
```

**How it works:**
- **L1 (local JSON)**: Checked first for instant access
- **L2 (DynamoDB)**: Checked on L1 miss, then written to L1; L1 hits are automatically backfilled to L2
- **Writes**: Saved to both L1 and L2 simultaneously
- **No table specified**: Works as local-only cache
- **Compression**: Payloads over 100KB are automatically gzip-compressed before writing to DynamoDB, reducing typical HTML payloads by 80-90%. A warning is logged if the compressed payload still exceeds DynamoDB's 400KB item limit.
- **save_on_del**: By default, `__del__` only saves to local JSON (L1). Set `save_on_del=True` to also write to DynamoDB on object destruction. Use `json_cache_save()` for explicit L1+L2 saves.

**DynamoDB table:**
- Auto-created if missing (requires IAM permissions)
- Partition key: `cache_id` (String)
- TTL enabled for automatic expiry
- Pay-per-request billing mode

**AWS credentials** via standard boto3 chain:
- Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- IAM role (recommended for EC2/Lambda)
- AWS credentials file (`~/.aws/credentials`)

### Custom TTL Configuration

```python
class WeatherService(JSONCache):
    @Cached(ttl=0.25)  # 6 hours (0.25 days)
    def get_forecast(self, city):
        return fetch_weather(city)
    
    @Cached(ttl=30)  # 30 days
    def get_historical(self, city, year):
        return fetch_historical(city, year)
```

### Excluding Variables from Cache

```python
class DataProcessor(JSONCache):
    def __init__(self):
        self._excluded_cache_vars = ["temp_data", "api_key"]
        super().__init__()
        self.results = {}
        self.temp_data = []  # Won't be cached
        self.api_key = "secret"  # Won't be cached
```

### Cache Management

```python
processor = DataProcessor()

# Get cache statistics
stats = processor.json_cache_stats()
print(stats)
# {'total_entries': 5, 'functions': {'process': 3, 'analyze': 2}}

# Clear specific function cache
processor.json_cache_clear("process")

# Clear all cache
processor.json_cache_clear()
```

### Cache Status Tracking

Detect whether a `@Cached` method returned cached data or executed the function, and which cache layer (L1/L2) was used:

```python
class DataService(JSONCache):
    def __init__(self):
        super().__init__(data_id="my-service", ttl=7)

    @Cached(ttl=7)
    def fetch(self, key: str) -> str:
        return expensive_operation(key)

svc = DataService()

# last_cache_status is None before any call
print(svc.last_cache_status)  # None

svc.fetch("foo")
print(svc.last_cache_status)  # "miss" (first run) or "l1" / "l2" (subsequent runs)

# Full per-call history keyed by function signature
print(svc.cache_status)
# {"fetch('foo',){}": "l1"}
```

**Status values:**
- `"l1"` — returned from local JSON cache
- `"l2"` — returned from DynamoDB cache
- `"miss"` — function was executed (no valid cache entry)
- `None` — no `@Cached` method has been called yet

`cache_status` is populated on init for all keys loaded from cache, and updated on every `@Cached` call. It is cleared when `json_cache_clear()` is called.

### Logging Control

```python
from cacherator import JSONCache

# Disable logging globally
JSONCache.set_logging(False)

# Enable logging globally (default)
JSONCache.set_logging(True)

# Per-instance control
processor = DataProcessor(logging=False)  # Silent mode
```

**When logging is enabled:**
- DynamoDB operations are logged (table creation, reads, writes)
- Local JSON operations are silent (fast, not interesting)

**When logging is disabled:**
- All operations are silent
```

## Configuration

### JSONCache Constructor

```python
JSONCache(
    data_id="unique_id",      # Unique identifier (default: class name)
    directory="cache",         # Cache directory (default: "data/cache")
    clear_cache=False,         # Clear existing cache on init
    ttl=999,                   # Default TTL in days
    logging=True,              # Enable logging (True/False)
    dynamodb_table=None,       # DynamoDB table name (optional)
    save_on_del=False          # Write to DynamoDB on __del__ (default: False)
)
```

### @Cached Decorator

```python
@Cached(
    ttl=7,                     # Time-to-live in days (default: class ttl)
    clear_cache=False          # Clear cache for this function
)
```

## Use Cases

### API Client with Caching

```python
class GitHubClient(JSONCache):
    def __init__(self):
        super().__init__(data_id="github_client", ttl=1)
    
    @Cached(ttl=0.5)  # 12 hours
    async def get_user(self, username):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.github.com/users/{username}") as resp:
                return await resp.json()
    
    @Cached(ttl=7)  # 1 week
    async def get_repos(self, username):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.github.com/users/{username}/repos") as resp:
                return await resp.json()
```

### Database Query Caching

```python
class UserRepository(JSONCache):
    def __init__(self):
        super().__init__(data_id="user_repo", ttl=0.1)  # 2.4 hours
    
    @Cached()
    def get_user_by_id(self, user_id):
        return db.query("SELECT * FROM users WHERE id = ?", user_id)
    
    @Cached(ttl=1)
    def get_user_stats(self, user_id):
        return db.query("SELECT COUNT(*) FROM posts WHERE user_id = ?", user_id)
```

### Machine Learning Model Predictions

```python
class ModelPredictor(JSONCache):
    def __init__(self):
        super().__init__(data_id="ml_predictor")
        self.model = load_model()
    
    @Cached(ttl=30)
    def predict(self, features_hash, features):
        # Cache predictions by feature hash
        return self.model.predict(features)
```

## Best Practices

### Recommended Use Cases

- Expensive API calls and network requests
- Database queries with relatively static data
- Heavy computational operations
- Machine learning model predictions
- Data transformations and aggregations

### When to Use TTL

- Set short TTL (minutes to hours) for frequently changing data
- Set long TTL (days to weeks) for stable reference data
- Consider data freshness requirements for your application

### What Not to Cache

- Non-deterministic functions (random number generation, timestamps)
- Very fast operations (overhead exceeds benefit)
- Non-JSON-serializable objects without custom handling
- Real-time data without appropriate TTL configuration

## Performance

Cacherator introduces minimal overhead:

- **Cache hit**: ~0.1ms
- **Cache miss**: Function execution time + ~1ms
- **Disk I/O**: Non-blocking, asynchronous operations

### Performance Improvements

- API calls (100ms - 5s) reduced to ~0.1ms
- Database queries (10ms - 1s) reduced to ~0.1ms
- Heavy computations (1s+) reduced to ~0.1ms

## Compatibility

- **Python**: 3.7 and above
- **Async**: Full support for async/await syntax
- **Operating Systems**: Windows, macOS, Linux
- **Data Types**: All JSON-serializable types plus datetime objects
- **Optional Dependencies**: boto3 (for DynamoDB backend), dynamorator

## Changelog

### Version 1.2.6

- **Added**: `cache_status` dict — per-function-signature hit/miss tracking with L1/L2 source, populated on init and updated on every `@Cached` call
- **Added**: `last_cache_status` — status of the most recent `@Cached` call (`"l1"`, `"l2"`, `"miss"`, or `None`)
- **Changed**: `json_cache_clear()` now also clears `cache_status` entries

### Version 1.2.5

- **Fixed**: L1 cache hits now automatically backfill L2 (DynamoDB) when enabled
- **Fixed**: Removed misleading `json_cache_save_db` branch in `@Cached` decorator — `json_cache_save()` is always used, which handles both L1 and L2

### Version 1.2.4

- **Added**: `save_on_del` parameter (default `False`) — `__del__` no longer writes to DynamoDB unless opted in, eliminating unnecessary writes on program exit
- **Changed**: `__del__` always saves to local JSON (L1); DynamoDB (L2) write requires explicit `json_cache_save()` or `save_on_del=True`
- **Removed**: Unreliable dirty-check on `json_cache_save()` — saves are now always performed when called

### Version 1.2.3

- **Added**: Automatic gzip compression for DynamoDB payloads exceeding 100KB
- **Added**: Warning logged when compressed payload still exceeds DynamoDB's 400KB limit
- **Added**: Compression is transparent — no API changes required

### Version 1.2.2

- **Fixed**: `json_cache_save()` now automatically syncs to DynamoDB (L2) when enabled
- **Deprecated**: `json_cache_save_db()` is now redundant (use `json_cache_save()` instead)

### Version 1.2.0

- **Added**: Optional DynamoDB backend for cross-machine cache sharing via dynamorator
- **Added**: Two-layer cache architecture (L1: local JSON, L2: DynamoDB)
- **Added**: Constructor parameter `dynamodb_table` for enabling DynamoDB
- **Added**: Automatic DynamoDB table creation with TTL support
- **Changed**: DynamoDB backend now uses dynamorator package
- **Changed**: Simplified logging to boolean (True/False)
- **Removed**: Environment variable configuration (use constructor parameter)
- **Removed**: LogLevel enum (simplified to boolean)

## Troubleshooting

### Cache Not Persisting

```python
# Explicitly save cache
obj.json_cache_save()

# Check for serialization errors
obj._excluded_cache_vars = ["problematic_attr"]
```

### Cache Not Being Used

```python
# Verify TTL hasn't expired
obj = MyClass(ttl=30)  # Increase TTL

# Ensure arguments are identical (type matters)
obj.func(1, 2)    # Different from
obj.func(1.0, 2)  # (int vs float)
```

### Large Cache Files

```python
# Exclude large attributes
self._excluded_cache_vars = ["large_data"]

# Use separate cache instances
processor1 = DataProcessor(data_id="dataset1")
processor2 = DataProcessor(data_id="dataset2")
```

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Resources

- **GitHub Repository**: https://github.com/Redundando/cacherator
- **Issue Tracker**: https://github.com/Redundando/cacherator/issues
- **PyPI Package**: https://pypi.org/project/cacherator/

---

Developed by [Arved Klöhn](https://github.com/Redundando)
