import asyncio
import os
from pprint import pprint

import aiohttp
from cacherator import Cached, JSONCache
from logorator import Logger


class Searcherator(JSONCache):

    def __init__(
            self,
            search_term="",
            num_results: int = 5,
            country: str | None = "us",
            language: str | None = "en",
            api_key: str | None = None,
            clear_cache=False,
            ttl=7):
        self.api_key = api_key
        if api_key is None:
            try:
                self.api_key = os.getenv("BRAVE_API_KEY")
            except KeyError:
                self.api_key = None
        self._search_results = None
        self._urls = None
        super().__init__(data_id=f"{search_term} ({language} {country} {num_results})", directory="data/search", clear_cache=clear_cache, ttl=ttl)
        self.search_term = search_term
        self.num_results = num_results
        self.language = language
        self.country = country

    def __str__(self):
        return f"Search: {self.search_term}"

    def __repr__(self):
        return self.__str__()

    @Logger()
    async def async_search(self):
        if self._search_results is None:
            url = 'https://api.search.brave.com/res/v1/web/search'
            headers = {'Accept': 'application/json', 'X-Subscription-Token': self.api_key, }
            params = {'q': self.search_term, 'count': self.num_results, 'country': self.country, 'search_lang': self.language, 'spellcheck': 'false'}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        self._search_results = await response.json()
                    else:
                        Logger.note(f"Error: {response.status} - {await response.text()}")
        return self._search_results

    async def urls(self):
        if self._urls is None:
            self._urls = []
            search_results = await self.search_result()
            for result in search_results.get("web", {}).get("results", []):
                self._urls.append(result["url"])
        return self._urls

    async def search_result(self):
        if self._search_results is None:
            self._search_results = await self.async_search()
        return self._search_results

    async def print(self):
        pprint(await self.search_result(), width=200, indent=2)


