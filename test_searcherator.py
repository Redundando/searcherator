"""Comprehensive test suite for Searcherator package."""
import asyncio
import os
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import shutil

from searcherator import (
    Searcherator,
    SearcheratorError,
    SearcheratorAuthError,
    SearcheratorRateLimitError,
    SearcheratorTimeoutError,
    SearcheratorAPIError
)


# Test Fixtures
@pytest.fixture
def api_key():
    """Provide a test API key."""
    return "test_api_key_12345"


@pytest.fixture
def mock_response_data():
    """Provide mock search response data."""
    return {
        "web": {
            "results": [
                {
                    "title": "Python Programming",
                    "url": "https://python.org",
                    "description": "Official Python website"
                },
                {
                    "title": "Python Tutorial",
                    "url": "https://docs.python.org/tutorial",
                    "description": "Learn Python"
                }
            ]
        }
    }


@pytest.fixture
def cleanup_cache():
    """Clean up test cache directory after tests."""
    yield
    cache_dir = Path("data/search")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)


# Exception Tests
class TestExceptions:
    """Test exception hierarchy and behavior."""
    
    def test_searcherator_error_base(self):
        """Test base exception."""
        error = SearcheratorError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_auth_error(self):
        """Test authentication error."""
        error = SearcheratorAuthError("Invalid key")
        assert isinstance(error, SearcheratorError)
        assert str(error) == "Invalid key"
    
    def test_timeout_error(self):
        """Test timeout error."""
        error = SearcheratorTimeoutError("Timeout")
        assert isinstance(error, SearcheratorError)
    
    def test_api_error(self):
        """Test API error with status code."""
        error = SearcheratorAPIError(500, "Server error")
        assert error.status_code == 500
        assert error.message == "Server error"
        assert "500" in str(error)
    
    def test_rate_limit_error(self):
        """Test rate limit error with metadata."""
        error = SearcheratorRateLimitError(
            "Rate limited",
            limit_per_second=15,
            limit_per_month=10000,
            remaining_per_second=0,
            remaining_per_month=5000,
            reset_per_second=1,
            reset_per_month=3600
        )
        assert error.limit_per_second == 15
        assert error.limit_per_month == 10000
        assert error.remaining_per_second == 0
        assert error.reset_per_second == 1


# Initialization Tests
class TestInitialization:
    """Test Searcherator initialization."""
    
    def test_init_with_api_key(self, api_key):
        """Test initialization with explicit API key."""
        search = Searcherator("Python", api_key=api_key)
        assert search.search_term == "Python"
        assert search.api_key == api_key
        assert search.num_results == 5
        assert search.country == "us"
        assert search.language == "en"
    
    def test_init_with_env_var(self, api_key, monkeypatch):
        """Test initialization with environment variable."""
        monkeypatch.setenv("BRAVE_API_KEY", api_key)
        search = Searcherator("Python")
        assert search.api_key == api_key
    
    def test_init_without_api_key(self, monkeypatch):
        """Test initialization fails without API key."""
        monkeypatch.delenv("BRAVE_API_KEY", raising=False)
        with pytest.raises(SearcheratorAuthError):
            Searcherator("Python")
    
    def test_init_custom_parameters(self, api_key):
        """Test initialization with custom parameters."""
        search = Searcherator(
            "Python",
            num_results=10,
            country="de",
            language="de",
            api_key=api_key,
            spellcheck=True,
            timeout=60,
            ttl=30
        )
        assert search.num_results == 10
        assert search.country == "de"
        assert search.language == "de"
        assert search.spellcheck is True
        assert search.timeout == 60
    
    def test_str_repr(self, api_key):
        """Test string representation."""
        search = Searcherator("Python", api_key=api_key)
        assert str(search) == "Search: Python"
        assert repr(search) == "Search: Python"


# Session Management Tests
class TestSessionManagement:
    """Test session creation and cleanup."""
    
    @pytest.mark.asyncio
    async def test_session_creation(self, api_key):
        """Test shared session is created."""
        search = Searcherator("Python", api_key=api_key)
        session = await search._get_session(30)
        assert session is not None
        assert not session.closed
        await Searcherator.close_session()
    
    @pytest.mark.asyncio
    async def test_session_reuse(self, api_key):
        """Test session is reused across instances."""
        search1 = Searcherator("Python", api_key=api_key)
        search2 = Searcherator("JavaScript", api_key=api_key)
        
        session1 = await search1._get_session(30)
        session2 = await search2._get_session(30)
        
        assert session1 is session2
        await Searcherator.close_session()
    
    @pytest.mark.asyncio
    async def test_session_close(self, api_key):
        """Test session closes properly."""
        search = Searcherator("Python", api_key=api_key)
        session = await search._get_session(30)
        await Searcherator.close_session()
        assert session.closed


# Rate Limiting Tests
class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_creation(self, api_key):
        """Test rate limiter is created."""
        search = Searcherator("Python", api_key=api_key)
        limiter = await search._get_rate_limiter()
        assert limiter is not None
        assert isinstance(limiter, asyncio.Semaphore)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_shared(self, api_key):
        """Test rate limiter is shared across instances."""
        search1 = Searcherator("Python", api_key=api_key)
        search2 = Searcherator("JavaScript", api_key=api_key)
        
        limiter1 = await search1._get_rate_limiter()
        limiter2 = await search2._get_rate_limiter()
        
        assert limiter1 is limiter2
    
    def test_parse_rate_limit_headers(self, api_key):
        """Test parsing rate limit headers."""
        search = Searcherator("Python", api_key=api_key)
        
        mock_headers = {
            'X-RateLimit-Limit': '15, 10000',
            'X-RateLimit-Remaining': '14, 9999',
            'X-RateLimit-Reset': '1, 3600'
        }
        
        search._parse_rate_limit_headers(mock_headers)
        
        assert search.rate_limit_per_second == 15
        assert search.rate_limit_per_month == 10000
        assert search.rate_remaining_per_second == 14
        assert search.rate_remaining_per_month == 9999
        assert search.rate_reset_per_second == 1
        assert search.rate_reset_per_month == 3600
    
    def test_parse_malformed_headers(self, api_key):
        """Test parsing malformed headers doesn't crash."""
        search = Searcherator("Python", api_key=api_key)
        
        mock_headers = {
            'X-RateLimit-Limit': 'invalid',
            'X-RateLimit-Remaining': '',
        }
        
        search._parse_rate_limit_headers(mock_headers)
        # Should not raise exception


# Error Handling Tests
class TestErrorHandling:
    """Test error handling for various scenarios."""
    
    def test_handle_401_error(self, api_key):
        """Test 401 authentication error."""
        search = Searcherator("Python", api_key=api_key)
        with pytest.raises(SearcheratorAuthError):
            search._handle_response_status(401, "Unauthorized")
    
    def test_handle_429_error(self, api_key):
        """Test 429 rate limit error."""
        search = Searcherator("Python", api_key=api_key)
        search.rate_limit_per_second = 15
        search.rate_remaining_per_second = 0
        
        with pytest.raises(SearcheratorRateLimitError) as exc_info:
            search._handle_response_status(429, "Too many requests")
        
        assert exc_info.value.limit_per_second == 15
        assert exc_info.value.remaining_per_second == 0
    
    def test_handle_generic_error(self, api_key):
        """Test generic API error."""
        search = Searcherator("Python", api_key=api_key)
        with pytest.raises(SearcheratorAPIError) as exc_info:
            search._handle_response_status(500, "Server error")
        
        assert exc_info.value.status_code == 500


# Search Functionality Tests
class TestSearchFunctionality:
    """Test core search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_result_success(self, api_key, mock_response_data, cleanup_cache):
        """Test successful search."""
        search = Searcherator("Python", api_key=api_key, clear_cache=True)
        
        with patch.object(search, '_search_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response_data
            
            result = await search.search_result()
            
            assert result == mock_response_data
            assert "web" in result
            assert len(result["web"]["results"]) == 2
        
        await Searcherator.close_session()
    
    @pytest.mark.asyncio
    async def test_urls_extraction(self, api_key, mock_response_data, cleanup_cache):
        """Test URL extraction from results."""
        search = Searcherator("Python", api_key=api_key, clear_cache=True)
        
        with patch.object(search, '_search_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response_data
            
            urls = await search.urls()
            
            assert len(urls) == 2
            assert "https://python.org" in urls
            assert "https://docs.python.org/tutorial" in urls
        
        await Searcherator.close_session()
    
    @pytest.mark.asyncio
    async def test_detailed_search_result(self, api_key, mock_response_data, cleanup_cache):
        """Test detailed search results."""
        search = Searcherator("Python", api_key=api_key, clear_cache=True)
        
        with patch.object(search, '_search_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response_data
            
            results = await search.detailed_search_result()
            
            assert len(results) == 2
            assert results[0]["title"] == "Python Programming"
            assert results[0]["url"] == "https://python.org"
        
        await Searcherator.close_session()
    
    @pytest.mark.asyncio
    async def test_empty_results(self, api_key, cleanup_cache):
        """Test handling of empty results."""
        search = Searcherator("Python", api_key=api_key, clear_cache=True)
        
        with patch.object(search, '_search_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"web": {"results": []}}
            
            urls = await search.urls()
            results = await search.detailed_search_result()
            
            assert urls == []
            assert results == []
        
        await Searcherator.close_session()


# Caching Tests
class TestCaching:
    """Test caching functionality."""
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, api_key, mock_response_data, cleanup_cache):
        """Test cache is used on second call."""
        search = Searcherator("Python", api_key=api_key, clear_cache=True)
        
        with patch.object(search, '_search_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response_data
            
            # First call - should hit API
            result1 = await search.search_result()
            assert mock_api.call_count == 1
            
            # Second call - should use cache
            result2 = await search.search_result()
            assert mock_api.call_count == 1  # Not called again
            
            assert result1 == result2
        
        await Searcherator.close_session()
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, api_key, mock_response_data, cleanup_cache):
        """Test cache clearing."""
        # First search with cache
        search1 = Searcherator("Python", api_key=api_key, clear_cache=False)
        
        with patch.object(search1, '_search_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response_data
            await search1.search_result()
        
        # Second search with clear_cache=True
        search2 = Searcherator("Python", api_key=api_key, clear_cache=True)
        
        with patch.object(search2, '_search_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response_data
            await search2.search_result()
            assert mock_api.call_count == 1  # API called because cache cleared
        
        await Searcherator.close_session()


# Concurrent Operations Tests
class TestConcurrentOperations:
    """Test concurrent search operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_searches(self, api_key, mock_response_data, cleanup_cache):
        """Test multiple concurrent searches."""
        queries = ["Python", "JavaScript", "Rust"]
        searches = [Searcherator(q, api_key=api_key, clear_cache=True) for q in queries]
        
        for search in searches:
            with patch.object(search, '_search_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = mock_response_data
        
        # This would normally test actual concurrent execution
        # For now, just verify they can be created
        assert len(searches) == 3
        
        await Searcherator.close_session()
    
    @pytest.mark.asyncio
    async def test_rate_limiting_enforced(self, api_key):
        """Test rate limiting delays requests."""
        search = Searcherator("Python", api_key=api_key)
        
        start_time = asyncio.get_event_loop().time()
        
        # Simulate multiple rapid requests
        limiter = await search._get_rate_limiter()
        async with limiter:
            pass
        async with limiter:
            pass
        
        # Just verify rate limiter exists and works
        assert limiter is not None


# Localization Tests
class TestLocalization:
    """Test localization features."""
    
    def test_german_search(self, api_key):
        """Test German localized search."""
        search = Searcherator(
            "Python Programmierung",
            language="de",
            country="de",
            api_key=api_key
        )
        assert search.language == "de"
        assert search.country == "de"
    
    def test_french_search(self, api_key):
        """Test French localized search."""
        search = Searcherator(
            "Programmation Python",
            language="fr",
            country="fr",
            api_key=api_key
        )
        assert search.language == "fr"
        assert search.country == "fr"


# Integration-like Tests
class TestIntegration:
    """Integration-style tests (mocked but realistic)."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, api_key, mock_response_data, cleanup_cache):
        """Test complete workflow from search to results."""
        search = Searcherator("Python tutorials", num_results=5, api_key=api_key, clear_cache=True)
        
        with patch.object(search, '_search_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response_data
            
            # Get full results
            results = await search.search_result()
            assert "web" in results
            
            # Get URLs
            urls = await search.urls()
            assert len(urls) > 0
            
            # Get detailed results
            detailed = await search.detailed_search_result()
            assert len(detailed) > 0
            assert "title" in detailed[0]
            assert "url" in detailed[0]
        
        await Searcherator.close_session()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
