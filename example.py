from searcherator import Searcherator
import asyncio
from pprint import pprint
async def main():
    # s = Searcherator("Book 'If Cats Disappeared from the World: A Novel' by 'Genki Kawamura'")
    h = Searcherator("Zusammenfassung Buch 'Demian' von 'Hermann Hesse'", language="de", country="de", num_results=10)
    search = Searcherator("site:audible.com/pd Harper Lee To Kill a Mockingbird", clear_cache=True)

    #await h.print()
    #pprint(await search.search_result(), width=200)
    print(await search.detailed_search_result())

if __name__ == "__main__":
    asyncio.run(main())
