import asyncio
import os
from pprint import pprint

import aiohttp
from cacherator import Cached, JSONCache
from logorator import Logger


class SearcheratorError(Exception):
    """Base exception for Searcherator errors."""
    pass


class SearcheratorTimeoutError(SearcheratorError):
    """Raised when a request times out."""
    pass


class SearcheratorAPIError(SearcheratorError):
    """Raised when the Brave Search API returns an error."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API error {status_code}: {message}")


class SearcheratorAuthError(SearcheratorError):
    """Raised when API authentication fails."""
    pass


class SearcheratorRateLimitError(SearcheratorError):
    """Raised when API rate limit is exceeded."""
    def __init__(self, message: str, limit_per_second: int = None, limit_per_month: int = None, 
                 remaining_per_second: int = None, remaining_per_month: int = None,
                 reset_per_second: int = None, reset_per_month: int = None):
        self.limit_per_second = limit_per_second
        self.limit_per_month = limit_per_month
        self.remaining_per_second = remaining_per_second
        self.remaining_per_month = remaining_per_month
        self.reset_per_second = reset_per_second
        self.reset_per_month = reset_per_month
        super().__init__(message)


class Searcherator(JSONCache):
    """Async web search client using the Brave Search API with built-in caching and rate limiting.
    
    Searcherator provides a simple interface to perform web searches with automatic caching,
    rate limiting, and connection pooling for efficient batch operations.
    
    Attributes:
        search_term (str): The search query string.
        num_results (int): Maximum number of results to return.
        country (str): Country code for localized results (e.g., 'us', 'de').
        language (str): Language code for results (e.g., 'en', 'de').
        spellcheck (bool): Whether to enable spell checking.
        timeout (int): Request timeout in seconds.
        rate_limit_per_second (int): Current per-second rate limit from API.
        rate_limit_per_month (int): Current monthly rate limit from API.
        rate_remaining_per_second (int): Remaining requests this second.
        rate_remaining_per_month (int): Remaining requests this month.
        rate_reset_per_second (int): Seconds until per-second limit resets.
        rate_reset_per_month (int): Seconds until monthly limit resets.
    
    Example:
        >>> import asyncio
        >>> from searcherator import Searcherator
        >>> 
        >>> async def main():
        ...     search = Searcherator("Python programming", num_results=5)
        ...     results = await search.search_result()
        ...     urls = await search.urls()
        ...     await Searcherator.close_session()
        >>> 
        >>> asyncio.run(main())
    """
    _rate_limiter: asyncio.Semaphore | None = None
    _rate_limiter_lock = asyncio.Lock()
    _last_request_time: float = 0
    _min_request_interval: float = 0.075  # 75ms between requests = ~13.3/sec (safe margin)
    _shared_session: aiohttp.ClientSession | None = None
    _session_lock = asyncio.Lock()

    def __init__(
            self,
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
            dynamodb_table: str | None = None):
        """Initialize a Searcherator instance.
        
        Args:
            search_term: The query string to search for.
            num_results: Maximum number of results to return (default: 5).
            country: Country code for search results (default: 'us').
            language: Language code for search results (default: 'en').
            api_key: Brave Search API key. If None, uses BRAVE_API_KEY environment variable.
            spellcheck: Enable spell checking on queries (default: False).
            timeout: Request timeout in seconds (default: 30).
            clear_cache: Clear existing cached results (default: False).
            ttl: Time-to-live for cached results in days (default: 7).
            logging: Enable cache operation logging (default: False).
            dynamodb_table: DynamoDB table name for cross-machine cache sharing (default: None).
        
        Raises:
            SearcheratorAuthError: If no API key is provided or found in environment.
        
        Example:
            >>> search = Searcherator(
            ...     "Python tutorials",
            ...     num_results=10,
            ...     country="de",
            ...     language="de"
            ... )
        """
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")

        if self.api_key is None:
            raise SearcheratorAuthError("api_key is required. Set BRAVE_API_KEY environment variable or pass api_key parameter.")

        self.search_term = search_term
        self.num_results = num_results
        self.language = language
        self.country = country
        self.spellcheck = spellcheck
        self.timeout = timeout
        self.rate_limit_per_second: int | None = None
        self.rate_limit_per_month: int | None = None
        self.rate_remaining_per_second: int | None = None
        self.rate_remaining_per_month: int | None = None
        self.rate_reset_per_second: int | None = None
        self.rate_reset_per_month: int | None = None
        super().__init__(data_id=f"{search_term} ({language} {country} {num_results})", directory="data/search", clear_cache=clear_cache, ttl=ttl, logging=logging, dynamodb_table=dynamodb_table)

    def __str__(self):
        return f"Search: {self.search_term}"

    def __repr__(self):
        return self.__str__()

    @classmethod
    async def _get_session(cls, timeout: int) -> aiohttp.ClientSession:
        """Get or create the shared aiohttp session."""
        async with cls._session_lock:
            if cls._shared_session is None or cls._shared_session.closed:
                timeout_config = aiohttp.ClientTimeout(total=timeout)
                cls._shared_session = aiohttp.ClientSession(timeout=timeout_config)
            return cls._shared_session

    @classmethod
    async def close_session(cls):
        """Close the shared aiohttp session.
        
        Call this method when done with all searches to properly clean up resources.
        Important for batch operations to prevent resource leaks.
        
        Example:
            >>> try:
            ...     results = await asyncio.gather(*[s.search_result() for s in searches])
            ... finally:
            ...     await Searcherator.close_session()
        """
        async with cls._session_lock:
            if cls._shared_session and not cls._shared_session.closed:
                await cls._shared_session.close()
                cls._shared_session = None

    @classmethod
    async def _get_rate_limiter(cls, limit: int = 20) -> asyncio.Semaphore:
        """Get or create the shared rate limiter semaphore."""
        async with cls._rate_limiter_lock:
            if cls._rate_limiter is None:
                cls._rate_limiter = asyncio.Semaphore(limit)
            return cls._rate_limiter

    @Cached()
    @Logger()
    async def search_result(self) -> dict:
        """Perform the search and return full results as a dictionary.
        
        This method is cached and rate-limited. Results are automatically cached
        based on the TTL setting. Rate limiting ensures API limits are respected.
        
        Returns:
            dict: Full search results from Brave Search API including metadata,
                web results, and other search information.
        
        Raises:
            SearcheratorAuthError: If API authentication fails.
            SearcheratorRateLimitError: If API rate limit is exceeded.
            SearcheratorTimeoutError: If request times out.
            SearcheratorAPIError: For other API errors.
        
        Example:
            >>> search = Searcherator("Python")
            >>> results = await search.search_result()
            >>> print(results['web']['results'][0]['title'])
        """
        rate_limiter = await self._get_rate_limiter()
        async with rate_limiter:
            # Ensure minimum time between request starts (not completions)
            async with self._rate_limiter_lock:
                now = asyncio.get_event_loop().time()
                time_since_last = now - self._last_request_time
                if time_since_last < self._min_request_interval:
                    await asyncio.sleep(self._min_request_interval - time_since_last)
                # Update timestamp BEFORE making the request
                self.__class__._last_request_time = asyncio.get_event_loop().time()
            
            return await self._search_api()

    def _parse_rate_limit_headers(self, headers) -> None:
        """Parse and store rate limit information from response headers."""
        try:
            limit_parts = headers.get('X-RateLimit-Limit', '').split(',')
            self.rate_limit_per_second = int(limit_parts[0].strip()) if len(limit_parts) > 0 and limit_parts[0].strip() else None
            self.rate_limit_per_month = int(limit_parts[1].strip()) if len(limit_parts) > 1 and limit_parts[1].strip() else None
            
            remaining_parts = headers.get('X-RateLimit-Remaining', '').split(',')
            self.rate_remaining_per_second = int(remaining_parts[0].strip()) if len(remaining_parts) > 0 and remaining_parts[0].strip() else None
            self.rate_remaining_per_month = int(remaining_parts[1].strip()) if len(remaining_parts) > 1 and remaining_parts[1].strip() else None
            
            reset_parts = headers.get('X-RateLimit-Reset', '').split(',')
            self.rate_reset_per_second = int(reset_parts[0].strip()) if len(reset_parts) > 0 and reset_parts[0].strip() else None
            self.rate_reset_per_month = int(reset_parts[1].strip()) if len(reset_parts) > 1 and reset_parts[1].strip() else None
        except (ValueError, IndexError):
            pass

    def _handle_response_status(self, status: int, error_text: str = "") -> None:
        """Raise appropriate exception based on response status code."""
        if status == 401:
            raise SearcheratorAuthError("Invalid API key")
        elif status == 429:
            raise SearcheratorRateLimitError(
                "API rate limit exceeded",
                limit_per_second=self.rate_limit_per_second,
                limit_per_month=self.rate_limit_per_month,
                remaining_per_second=self.rate_remaining_per_second,
                remaining_per_month=self.rate_remaining_per_month,
                reset_per_second=self.rate_reset_per_second,
                reset_per_month=self.rate_reset_per_month
            )
        else:
            Logger.note(f"Error: {status} - {error_text}")
            raise SearcheratorAPIError(status, error_text)

    async def _search_api(self) -> dict:
        url = 'https://api.search.brave.com/res/v1/web/search'
        headers = {'Accept': 'application/json', 'X-Subscription-Token': self.api_key}
        params = {'q': self.search_term, 'count': self.num_results, 'country': self.country, 'search_lang': self.language, 'spellcheck': str(self.spellcheck).lower()}
        
        session = await self._get_session(self.timeout)
        
        try:
            async with session.get(url, headers=headers, params=params) as response:
                self._parse_rate_limit_headers(response.headers)
                
                if response.status == 200:
                    result = await response.json()
                    self.json_cache_save()
                    return result
                else:
                    error_text = await response.text()
                    self._handle_response_status(response.status, error_text)
        except asyncio.TimeoutError:
            raise SearcheratorTimeoutError(f"Request timed out after {self.timeout} seconds")
        except aiohttp.ClientError as e:
            raise SearcheratorAPIError(0, f"Network error: {str(e)}")

    async def urls(self) -> list[str]:
        """Get a list of URLs from the search results.
        
        Returns:
            list[str]: List of URLs from the search results.
        
        Example:
            >>> search = Searcherator("Python tutorials")
            >>> urls = await search.urls()
            >>> print(urls[0])
        """
        search_results = await self.search_result()
        return [result["url"] for result in search_results.get("web", {}).get("results", [])]

    async def detailed_search_result(self) -> list[dict]:
        """Get detailed information for each search result.
        
        Returns:
            list[dict]: List of result dictionaries containing title, URL,
                description, and other metadata for each result.
        
        Example:
            >>> search = Searcherator("Python")
            >>> results = await search.detailed_search_result()
            >>> for result in results:
            ...     print(f"{result['title']}: {result['url']}")
        """
        search_results = await self.search_result()
        return search_results.get("web", {}).get("results", [])

    async def print(self) -> None:
        """Pretty print the full search results.
        
        Prints the complete search results in a formatted, readable way.
        Useful for debugging and exploration.
        
        Example:
            >>> search = Searcherator("Python")
            >>> await search.print()
        """
        pprint(await self.search_result(), width=200, indent=2)


